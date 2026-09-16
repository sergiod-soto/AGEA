# Infraestructura/Gestores/Mundo/LogicaMundo/logica_mundo.py

from __future__ import annotations

import asyncio
import datetime
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from numpy import uint64

from Core.Entities.Mundo.mundo import Mundo
from Core.Entities.Mundo.Celda.celda import Celda
from Core.Entities.Mundo.Celda.celda_atmosfera import Celda_Atmosfera
from Core.Entities.Elementos.elemento import Elemento
from Core.Entities.Elementos.registry import reconstruir_elemento
from Core.Entities.entity import Modos
from Infraestructura.Gestores.Mundo.Sector.mutaciones import (
    CrearElemento,
    EliminarElemento,
    MoverElemento,
    Mutacion,
)
from Infraestructura.Gestores.Transporte.gestor_bots_client_async import (
    GestorBotsClientAsync,
)
from Infraestructura.Gestores.tipos_comunes import ActionResult
import Config.settings as config

logger = logging.getLogger(__name__)


@dataclass
class GlobalEvent:
    event_id: str
    type: str
    pos: Optional[tuple[int, int]]
    payload: bytes


class ElementoGlobal:
    def tick(self, tick_id: int) -> dict:
        raise NotImplementedError

    def to_snapshot(self) -> dict:
        raise NotImplementedError

    @classmethod
    def from_snapshot(cls, data: dict) -> "ElementoGlobal":
        raise NotImplementedError


class LogicaMundo:

    def __init__(
        self,
        gestor_bots_client: "GestorBotsClientAsync | None" = None,
        poblar_suelo: bool = False,
        mundo: "Mundo | None" = None,
    ):
        self.SNAPSHOT_DIR = Path(config.SNAPSHOT_DIR)

        # Todo el estado espacial (celdas de terreno, celdas de atmósfera,
        # elementos por id, posiciones, y la traducción bot_id -> id_elemento)
        # vive en Mundo -- síncrono, sin lock propio. LogicaMundo se queda con
        # lo que no es "grid": el lock async, el contador de ids, snapshots,
        # sonido, eventos globales y ciclo de vida de bots.
        self.mundo: Mundo = mundo or Mundo()

        self._id_counter: uint64 = uint64(0)

        self._active_events: dict[str, GlobalEvent] = {}
        self._event_counter: int = 0

        self._elementos_globales: dict[str, ElementoGlobal] = {}
        self._tick_actual: int = 0

        self._gestor_bots_client = gestor_bots_client

        self._lock: asyncio.Lock = asyncio.Lock()

        if poblar_suelo:
            self._poblar_suelo()

        logger.info("LogicaMundo inicializado.")

    @staticmethod
    def _bot_id_de(elemento: Any) -> Optional[int]:
        """Extrae el bot_id (stat 'id') de un elemento ya reconstruido.
        Devuelve None solo si el elemento no es un Bot o no tiene ese stat --
        se comprueba explícitamente con tiene_stat() para que un fallo real
        (p.ej. stats sin inicializar) siga reventando en vez de esconderse
        detrás de un "no es un bot"."""
        if not hasattr(elemento, "tiene_stat") or not elemento.tiene_stat("id"):
            return None
        return int(elemento.get_stat("id"))

    # ---- Aplicación de deltas de Sector ----

    async def aplicar_delta_sector(self, mutaciones: list[Mutacion]) -> None:
        async with self._lock:
            for m in mutaciones:
                if isinstance(m, CrearElemento):
                    self._aplicar_crear_sin_lock(m)
                elif isinstance(m, EliminarElemento):
                    self._aplicar_eliminar_sin_lock(m)
                elif isinstance(m, MoverElemento):
                    self._aplicar_mover_sin_lock(m)
                else:
                    logger.warning(
                        "aplicar_delta_sector: tipo de mutación desconocido: %r", m
                    )

    def _aplicar_crear_sin_lock(self, m: CrearElemento) -> None:
        """Solo debe llamarse ya dentro de self._lock."""
        self._id_counter += 1
        eid = self._id_counter
        m.elemento.id_elemento = eid  # el objeto llega sin id -- se asigna aquí
        self._registrar_sonidos_de(m.elemento)

        bot_id = None
        if m.tipo_slot == "bot":
            bot_id = self._bot_id_de(m.elemento)
            if bot_id is None:
                logger.warning(
                    "aplicar_delta_sector: elemento bot en %s sin bot_id "
                    "extraíble -- no se indexa por bot_id.",
                    m.pos,
                )

        self.mundo.crear_elemento(eid, m.pos, m.tipo_slot, m.elemento, bot_id=bot_id)
        logger.debug(
            "Elemento %s creado en %s (marcador_local=%s)", eid, m.pos, m.marcador_local
        )

    def _aplicar_eliminar_sin_lock(self, m: EliminarElemento) -> None:
        """Solo debe llamarse ya dentro de self._lock."""
        elemento = self.mundo.obtener_elemento(m.id_elemento)
        if elemento is None:
            logger.warning(
                "aplicar_delta_sector: elemento %s no encontrado para eliminar en %s",
                m.id_elemento,
                m.pos,
            )
            return

        try:
            self._liberar_sonidos_de(elemento)
        except Exception as exc:
            raise ValueError(f"Error eliminando sonidos de {elemento}") from exc

        # bot_id se resuelve ANTES de eliminar, a partir del objeto que aún
        # tenemos -- después de eliminar ya no habría forma de recuperarlo.
        bot_id = self._bot_id_de(elemento)
        if not self.mundo.eliminar_elemento(m.id_elemento, bot_id=bot_id):
            logger.warning(
                "aplicar_delta_sector: elemento %s no encontrado en %s",
                m.id_elemento,
                m.pos,
            )

    def _aplicar_mover_sin_lock(self, m: MoverElemento) -> None:
        """Solo debe llamarse ya dentro de self._lock."""
        if not self.mundo.mover_elemento(m.id_elemento, m.pos_destino):
            logger.warning(
                "aplicar_delta_sector: elemento %s no encontrado en %s",
                m.id_elemento,
                m.pos_origen,
            )

    # ---- Traducción Cell (proto) <-> Celda (interno) ----

    def _slot_bytes_a_id(self, blob: bytes) -> Optional[uint64]:
        # Blob vacío = "slot desocupado" (ver common.proto), no un error.
        if not blob:
            return None
        data = json.loads(blob.decode())
        elemento = reconstruir_elemento(data)
        eid = getattr(elemento, "id_elemento", None)
        if eid is None:
            raise ValueError(
                f"Elemento deserializado sin 'id_elemento' (clase={data.get('__clase__')!r})."
            )
        self.mundo.registrar_elemento_reconstruido(eid, elemento)
        return eid

    def _id_a_slot_bytes(self, eid: Optional[uint64]) -> bytes:
        if eid is None:
            return b""
        elemento = self.mundo.obtener_elemento(eid)
        if elemento is None:
            logger.warning("_id_a_slot_bytes: elemento %s no encontrado.", eid)
            return b""
        return json.dumps(elemento.serializar(modo=Modos.transporte)).encode()

    def _cell_a_celda(self, cell) -> Celda:
        return Celda(
            suelo=self._slot_bytes_a_id(cell.suelo),
            bot=self._slot_bytes_a_id(cell.bot),
            resto=[
                eid
                for eid in (self._slot_bytes_a_id(blob) for blob in cell.resto)
                if eid is not None
            ],
        )

    def _celda_a_cell(self, pos: tuple[int, int], celda: Celda):
        from Infraestructura.Gestores.Transporte.Proto_Generated import (
            common_pb2 as common_pb,
        )

        x, y = pos
        return common_pb.Cell(  # type: ignore
            pos=common_pb.Position(x=x, y=y),  # type: ignore
            suelo=self._id_a_slot_bytes(celda.suelo),
            bot=self._id_a_slot_bytes(celda.bot),
            resto=[self._id_a_slot_bytes(eid) for eid in celda.resto],
        )

    # ---- Identidad ----

    async def asignar_id(self) -> uint64:
        async with self._lock:
            self._id_counter += 1
            return self._id_counter

    # ---- Elementos ----

    async def crear_elemento(
        self, pos: tuple[int, int], type_id: str, element: bytes
    ) -> tuple[bool, str]:
        async with self._lock:
            try:
                eid = self._slot_bytes_a_id(element)
            except (ValueError, json.JSONDecodeError) as exc:
                return False, f"Elemento inválido: {exc}"

            if eid is None:
                return False, "El elemento no tiene 'id' asignado."

            elemento = self.mundo.obtener_elemento(eid)
            self._registrar_sonidos_de(elemento)

            bot_id = None
            if type_id == "bot":
                bot_id = self._bot_id_de(elemento)
                if bot_id is None:
                    logger.warning(
                        "crear_elemento: bot en %s sin bot_id extraíble -- "
                        "no se indexa por bot_id.",
                        pos,
                    )

            self.mundo.crear_elemento(eid, pos, type_id, elemento, bot_id=bot_id)
            logger.debug("Elemento %s creado en %s (type_id=%s)", eid, pos, type_id)
            return True, ""

    async def construir_elemento(
        self,
        pos: tuple[int, int],
        nombre_clase: str,
        campos: dict,
    ) -> tuple[bool, str, Optional[uint64]]:
        """Crea un elemento NUEVO llamando a su __init__ real.

        FIX respecto al original: si el elemento construido es un bot,
        ahora SÍ se indexa su bot_id (antes no se hacía, dejando ese bot
        invisible para eliminar_avatar_bot/matar_bot/resolver_accion)."""
        from Core.Entities.Elementos.registry import construir_elemento

        async with self._lock:
            self._id_counter += 1
            eid = self._id_counter

            campos_normalizados = {
                k: tuple(v) if isinstance(v, list) else v for k, v in campos.items()
            }

            try:
                elemento = construir_elemento(
                    nombre_clase, id_elemento=eid, **campos_normalizados
                )
            except (ValueError, TypeError) as exc:
                return False, f"No se pudo construir '{nombre_clase}': {exc}", None

            self._registrar_sonidos_de(elemento)

            tipo_slot = elemento.tipo_slot()
            bot_id = None
            if tipo_slot == "bot":
                bot_id = self._bot_id_de(elemento)
                if bot_id is None:
                    logger.warning(
                        "construir_elemento: bot en %s sin bot_id extraíble -- "
                        "no se indexa por bot_id.",
                        pos,
                    )

            self.mundo.crear_elemento(eid, pos, tipo_slot, elemento, bot_id=bot_id)
            logger.debug(
                "Elemento %s (%s) construido en %s (slot=%s)",
                eid,
                nombre_clase,
                pos,
                tipo_slot,
            )
            return True, "", eid

    async def modificar_elemento(
        self, pos: tuple[int, int], element_id: uint64, patch: dict
    ) -> tuple[bool, str]:
        async with self._lock:
            if not self.mundo.contiene(pos, element_id):
                return False, f"Elemento {element_id} no encontrado en {pos}."

            elemento = self.mundo.obtener_elemento(element_id)
            if elemento is None:
                return False, f"Elemento {element_id} no encontrado en el registro."

            elemento.aplicar_patch(patch)
            return True, ""

    def _eliminar_elemento_sin_lock(
        self, pos: tuple[int, int], element_id: uint64
    ) -> tuple[bool, str]:
        """Cuerpo real de eliminar_elemento, factorizado para poder llamarlo
        también desde eliminar_avatar_bot bajo el MISMO lock -- así se evita
        la race condition del original, donde resolver bot_id->pos y borrar
        eran dos secciones de lock separadas y otra corrutina podía mover o
        eliminar el elemento justo entre medias."""
        if not self.mundo.contiene(pos, element_id):
            return False, f"Elemento {element_id} no encontrado en {pos}."

        elemento = self.mundo.obtener_elemento(element_id)
        if elemento is not None:
            self._liberar_sonidos_de(elemento)

        bot_id = self._bot_id_de(elemento) if elemento is not None else None
        self.mundo.eliminar_elemento(element_id, bot_id=bot_id)
        return True, ""

    async def eliminar_elemento(
        self, pos: tuple[int, int], element_id: uint64
    ) -> tuple[bool, str]:
        async with self._lock:
            return self._eliminar_elemento_sin_lock(pos, element_id)

    async def eliminar_avatar_bot(self, bot_id: int) -> tuple[bool, str]:
        bot_id = int(bot_id)
        async with self._lock:
            eid = self.mundo.id_elemento_de_bot(bot_id)
            if eid is None:
                return False, f"Bot {bot_id!r} no encontrado."
            pos = self.mundo.obtener_posicion(eid)
            if pos is None:
                return False, f"Bot {bot_id!r} sin posición registrada."
            return self._eliminar_elemento_sin_lock(pos, eid)

    async def matar_bot(
        self, bot_id: int, cause: str, tick_id: int
    ) -> tuple[bool, str]:
        ok, error = await self.eliminar_avatar_bot(bot_id)
        if not ok:
            logger.error(
                "matar_bot: no se pudo eliminar avatar de %s: %s", bot_id, error
            )
            return False, error

        if self._gestor_bots_client is None:
            logger.warning(
                "matar_bot: sin gestor_bots_client configurado -- el script "
                "del bot %s no será terminado.",
                bot_id,
            )
            return True, ""

        try:
            await self._gestor_bots_client.matar_script_bot(bot_id)
        except Exception as exc:
            logger.error(
                "matar_bot: error pidiendo matar script de %s: %s", bot_id, exc
            )
            return False, str(exc)

        logger.info("Bot %s eliminado (causa=%s, tick=%d).", bot_id, cause, tick_id)
        return True, ""

    # ---- Sonido ----

    async def obtener_audio(self, id_sonido: str) -> tuple[bool, str, bytes]:
        if not self._cache_audio.tiene(id_sonido):
            return (
                False,
                f"id_sonido '{id_sonido}' no encontrado en la biblioteca.",
                b"",
            )
        audio = self._cache_audio.obtener(id_sonido)
        return True, "", json.dumps(audio).encode()

    def _liberar_sonidos_de(self, elemento) -> None:
        if hasattr(elemento, "todos_los_sonidos"):
            for sonido in elemento.todos_los_sonidos():
                sonido.liberar_de_biblioteca()

    def _registrar_sonidos_de(self, elemento) -> None:
        if hasattr(elemento, "todos_los_sonidos"):
            for sonido in elemento.todos_los_sonidos():
                sonido.guardar_en_biblioteca()

    # ---- Acciones de bots ----

    async def resolver_accion(
        self, bot_id: int, action_type: str, payload: bytes
    ) -> ActionResult:
        from Infraestructura.Gestores.Mundo.LogicaMundo.api_acciones import (
            ACCIONES,
            AccionContext,
        )

        entrada = ACCIONES.get(action_type)
        if entrada is None:
            logger.warning(
                "resolver_accion: acción desconocida '%s' (bot %s)", action_type, bot_id
            )
            return ActionResult(ok=False, error=f"Acción desconocida: {action_type}")

        fn = entrada.get("funcion")
        if fn is None:
            return ActionResult(
                ok=False,
                error=f"Acción '{action_type}' no ejecutable por Logica_Mundo.",
            )

        # TODO(rendimiento): con miles de bots, reconstruir bot_positions
        # ENTERO en cada acción de un solo bot es O(n_bots) desperdiciado
        # por llamada. Pendiente de ver api_acciones.py para saber si
        # ACCIONES realmente necesita el dict completo o solo la posición
        # del bot que actúa -- si es lo segundo, esto se sustituye por un
        # simple self.mundo.obtener_posicion(eid) bajo demanda.
        ctx = AccionContext(
            bot_id=bot_id,
            payload=payload,
            gold_cells=self.mundo.malla_terreno,
            elements=self.mundo.elementos,
            bot_positions={
                bid: self.mundo.ids[eid]
                for bid, eid in self.mundo.bots.items()
                if eid in self.mundo.ids
            },
        )

        try:
            async with self._lock:
                return await fn(ctx)
        except Exception as exc:
            logger.error(
                "Error en resolver_accion '%s' para bot %s: %s",
                action_type,
                bot_id,
                exc,
            )
            return ActionResult(ok=False, error=str(exc))

    # ---- Eventos globales ----

    async def spawn_global_event(
        self, type_: str, pos: Optional[tuple[int, int]], payload: bytes
    ) -> tuple[bool, str, str]:
        async with self._lock:
            self._event_counter += 1
            event_id = f"evt_{self._event_counter:06d}"
            self._active_events[event_id] = GlobalEvent(
                event_id=event_id, type=type_, pos=pos, payload=payload
            )
            logger.info("Evento global '%s' creado (%s)", event_id, type_)
            return True, "", event_id

    async def despawn_global_event(
        self, event_id: str, reason: str
    ) -> tuple[bool, str]:
        async with self._lock:
            if event_id not in self._active_events:
                return False, f"Evento '{event_id}' no encontrado."
            del self._active_events[event_id]
            logger.info("Evento global '%s' finalizado (%s)", event_id, reason)
            return True, ""

    async def get_active_events(self) -> list[GlobalEvent]:
        async with self._lock:
            return list(self._active_events.values())

    # ---- Elementos globales ----

    async def avanzar_elementos_globales(self, tick_id: int) -> dict:
        cambios: dict = {}
        async with self._lock:
            self._tick_actual = tick_id
            for elem in self._elementos_globales.values():
                cambios.update(elem.tick(tick_id))
        return cambios

    async def get_tick_actual(self) -> int:
        async with self._lock:
            return self._tick_actual

    async def get_elementos_globales(self) -> dict[str, dict]:
        async with self._lock:
            return {
                nombre: elem.to_snapshot()
                for nombre, elem in self._elementos_globales.items()
            }

    # ---- Atmósfera (una sola definición de cada método -- el original
    # tenía crear_atmosfera/obtener_atmosfera/actualizar_atmosfera
    # duplicados literalmente dos veces; era código muerto inofensivo
    # pero confuso, se elimina la copia) ----

    async def crear_atmosfera(
        self,
        pos_atmosfera: tuple[int, int],
        resistencia_viento: float,
        direccion_preferente_viento: Any,
        fuerza_viento: Any,
        bioma: Any,
    ) -> tuple[bool, str]:
        async with self._lock:
            if self.mundo.obtener_atmosfera(pos_atmosfera) is not None:
                logger.warning(
                    "crear_atmosfera: ya existía una celda en %s -- se sobrescribe.",
                    pos_atmosfera,
                )
            self.mundo.crear_atmosfera(
                pos_atmosfera,
                resistencia_viento,
                direccion_preferente_viento,
                fuerza_viento,
                bioma,
            )
            return True, ""

    async def obtener_atmosfera(
        self, pos_suelo: tuple[int, int]
    ) -> tuple[bool, str, Optional[Celda_Atmosfera]]:
        pos_atmosfera = self.mundo.pos_suelo_a_atmosfera(pos_suelo)
        async with self._lock:
            celda = self.mundo.obtener_atmosfera(pos_atmosfera)
            if celda is None:
                return (
                    False,
                    f"No hay celda de atmósfera para {pos_suelo} (bloque {pos_atmosfera}).",
                    None,
                )
            return True, "", celda

    async def actualizar_atmosfera(
        self, pos_suelo: tuple[int, int], patch: dict
    ) -> tuple[bool, str]:
        pos_atmosfera = self.mundo.pos_suelo_a_atmosfera(pos_suelo)
        async with self._lock:
            celda = self.mundo.obtener_atmosfera(pos_atmosfera)
            if celda is None:
                return (
                    False,
                    f"No hay celda de atmósfera para {pos_suelo} (bloque {pos_atmosfera}).",
                )
            celda.aplicar_patch(patch)
            return True, ""

    # ---- Región / representación ----

    async def obtener_celdas_en_region(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        excluir_min: Optional[tuple[int, int]] = None,
        excluir_max: Optional[tuple[int, int]] = None,
    ) -> list:
        async with self._lock:
            return [
                self._celda_a_cell(pos, celda)
                for pos, celda in self.mundo.celdas_en_region(
                    min_pos, max_pos, excluir_min, excluir_max
                )
            ]

    async def actualizar_celdas(self, changed_cells: list) -> None:
        async with self._lock:
            for cell in changed_cells:
                pos = (cell.pos.x, cell.pos.y)
                celda = self._cell_a_celda(cell)
                self.mundo.actualizar_celda(pos, celda)

    async def consultar_representacion(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str],
        modo: str,
        tipos: list[str] | None = None,
    ) -> bytes:
        x0, y0 = min_pos
        x1, y1 = max_pos

        elementos = []
        suelo_resultado = []
        atmosfera = []  # TODO: representar sistema atmosferico

        async with self._lock:
            for (x, y), celda in self.mundo.malla_terreno.items():
                if not (x0 <= x < x1 and y0 <= y < y1):
                    continue

                if celda.suelo is not None:
                    suelo_elemento = self.mundo.obtener_elemento(celda.suelo)
                    if suelo_elemento is not None and (
                        tipos is None or type(suelo_elemento).__name__ in tipos
                    ):
                        campos = suelo_elemento.representacion(modo, incluir)
                        if campos.get("elemento") or campos.get("comportamientos"):
                            suelo_resultado.append({**campos})

                for eid in (celda.bot, *celda.resto):
                    elemento: Elemento = self.mundo.obtener_elemento(eid)
                    if elemento is None:
                        continue
                    if tipos is not None and type(elemento).__name__ not in tipos:
                        continue
                    campos = elemento.representacion(incluir)
                    if not campos.get("elemento") and not campos.get("comportamientos"):
                        continue
                    elementos.append({**campos})

            return json.dumps(
                {
                    "modo": modo,
                    "elementos": elementos,
                    "suelo": suelo_resultado,
                    "atmosfera": atmosfera,
                }
            ).encode()

    async def obtener_elemento(
        self,
        element_id: uint64,
        tipo_datos: str = "representacion",
        incluir: list[str] | None = None,
    ) -> tuple[bool, str, bytes]:
        async with self._lock:
            elemento = self.mundo.obtener_elemento(element_id)
            if elemento is None:
                return False, f"Elemento {element_id} no encontrado.", b""

            if tipo_datos == "serializacion":
                datos = elemento.serializar(modo=Modos.guardado)
            elif tipo_datos == "representacion":
                datos = elemento.representacion(
                    modo=Modos.transporte, incluir=incluir or []
                )
            else:
                return (
                    False,
                    f"tipo_datos desconocido: '{tipo_datos}' "
                    "(usa 'representacion' o 'serializacion').",
                    b"",
                )

        return True, "", json.dumps(datos, ensure_ascii=False).encode()

    # ---- Snapshots ----

    async def save_snapshot(self, snapshot_id: str) -> None:
        self.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        path = self.SNAPSHOT_DIR / f"logica_mundo_{snapshot_id}.json"

        async with self._lock:
            data = {
                "snapshot_id": snapshot_id,
                "fecha": datetime.datetime.now().isoformat(),
                "id_counter": int(self._id_counter),
                "gold_cells": {
                    f"{x},{y}": {
                        "suelo": int(celda.suelo) if celda.suelo is not None else None,
                        "bot": int(celda.bot) if celda.bot is not None else None,
                        "resto": [int(eid) for eid in celda.resto],
                    }
                    for (x, y), celda in self.mundo.malla_terreno.items()
                },
                "elements": {
                    str(eid): elemento.serializar(modo=Modos.guardado)
                    for eid, elemento in self.mundo.elementos.items()
                },
                # Se deriva de ids+bots -- ya no existe un dict propio de
                # posiciones de bot, ver decisión de mantener 2 dicts (A).
                "bot_positions": {
                    bid: list(self.mundo.ids[eid])
                    for bid, eid in self.mundo.bots.items()
                    if eid in self.mundo.ids
                },
                "active_events": {
                    eid: {
                        "type": ev.type,
                        "pos": list(ev.pos) if ev.pos else None,
                        "payload": ev.payload.hex(),
                    }
                    for eid, ev in self._active_events.items()
                },
                "elementos_globales": {
                    nombre: elem.to_snapshot()
                    for nombre, elem in self._elementos_globales.items()
                },
            }

        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        logger.info("Snapshot de Logica_Mundo guardado: %s", path)
        self._purgar_snapshots_antiguos()

    def _purgar_snapshots_antiguos(self) -> None:
        snapshots = sorted(
            self.SNAPSHOT_DIR.glob("logica_mundo_*.json"),
            key=lambda p: p.stem.removeprefix("logica_mundo_"),
        )
        sobrantes = len(snapshots) - config.SNAPSHOT_MAX
        for path in snapshots[:sobrantes]:
            path.unlink(missing_ok=True)
            logger.debug("Snapshot antiguo purgado: %s", path)

    async def load_state(self, snapshot_id: str) -> None:
        path = self.SNAPSHOT_DIR / f"logica_mundo_{snapshot_id}.json"
        if not path.exists():
            logger.warning("Snapshot '%s' no encontrado en %s.", snapshot_id, path)
            return

        data = json.loads(path.read_text())

        async with self._lock:
            # NOTA (pendiente, no crítico): esto asigna un int normal,
            # rompiendo el invariante "siempre uint64" que se mantiene en
            # el resto del ciclo de vida. No falla porque uint64 e int se
            # comparan/hashean igual para el mismo valor, pero conviene
            # normalizarlo si en algún momento se añade un isinstance().
            self._id_counter = data.get("id_counter", 0)

            self.mundo.elementos = {
                int(eid): reconstruir_elemento(edata)
                for eid, edata in data.get("elements", {}).items()
            }

            self.mundo.malla_terreno = {
                tuple(map(int, k.split(","))): Celda(
                    suelo=v["suelo"], bot=v["bot"], resto=v["resto"]
                )
                for k, v in data.get("gold_cells", {}).items()
            }

            self.mundo.ids = {}
            for pos, celda in self.mundo.malla_terreno.items():
                for eid in (celda.suelo, celda.bot, *celda.resto):
                    if eid is not None:
                        self.mundo.ids[eid] = pos

            self.mundo.bots = {}
            for bid_str, pos in data.get("bot_positions", {}).items():
                bid = int(bid_str)
                pos_t = tuple(pos)
                celda = self.mundo.malla_terreno.get(pos_t)
                eid = celda.bot if celda is not None else None
                if eid is not None:
                    self.mundo.bots[bid] = eid
                else:
                    logger.warning(
                        "load_state: bot %s en %s sin elemento 'bot' en esa "
                        "celda -- no se restaura.",
                        bid,
                        pos_t,
                    )

            self._active_events = {
                eid: GlobalEvent(
                    event_id=eid,
                    type=ev["type"],
                    pos=tuple(ev["pos"]) if ev["pos"] else None,
                    payload=bytes.fromhex(ev["payload"]),
                )
                for eid, ev in data.get("active_events", {}).items()
            }

            eg_data = data.get("elementos_globales", {})
            for nombre, elem in self._elementos_globales.items():
                if nombre in eg_data:
                    elem.__dict__.update(elem.from_snapshot(eg_data[nombre]).__dict__)

        logger.info("Estado de Logica_Mundo restaurado desde %s", path)

    def _poblar_suelo(self) -> None:
        # TODO: parche temporal. Falta un generador de suelo en condiciones.
        logger.info(
            "Suelo poblado: %d x %d celdas (%d elementos Suelo creados).",
            config.GRID_WIDTH,
            config.GRID_HEIGHT,
            config.GRID_WIDTH * config.GRID_HEIGHT,
        )
