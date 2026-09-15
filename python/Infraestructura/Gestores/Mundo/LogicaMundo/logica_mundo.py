# Infraestructura/Gestores/Mundo/LogicaMundo/logica_mundo.py


from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from numpy import uint64

from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo_cesped import Suelo_Cesped
from Core.Entities.Elementos.Abstractos.Informacion.sonido import Sonido
from Core.Entities.Elementos.elemento import Elemento
from Core.Entities.Elementos.registry import reconstruir_elemento
from Core.Entities.entity import Modos
from Services.Elemento.cache_audio import CacheAudio
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
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo

logger = logging.getLogger(__name__)


@dataclass
class Celda:
    suelo: Optional[uint64] = None
    bot: Optional[uint64] = None
    resto: list[uint64] = field(default_factory=list)


@dataclass
class GlobalEvent:
    event_id: str
    type: str
    pos: Optional[tuple[int, int]]
    payload: bytes


class ElementoGlobal:
    def tick(self, tick_id: int) -> dict:
        """TODO: tick()"""
        raise NotImplementedError

    def to_snapshot(self) -> dict:
        """TODO: to_snapshot()"""
        raise NotImplementedError

    @classmethod
    def from_snapshot(cls, data: dict) -> "ElementoGlobal":
        """TODO: from_snapshot()"""
        raise NotImplementedError


class LogicaMundo:

    def __init__(
        self,
        gestor_bots_client: "GestorBotsClientAsync | None" = None,
        poblar_suelo: bool = False,
    ):
        self.SNAPSHOT_DIR = Path(config.SNAPSHOT_DIR)

        self._gold_cells: dict[tuple[int, int], Celda] = {}
        self._elements: dict[uint64, Any] = {}
        self._bot_positions: dict[str, tuple[int, int]] = {}
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
        """
        Extrae el bot_id (stat 'id', ver Bot.__init__ / serialize_all) de un
        elemento ya reconstruido. Devuelve None solo en el caso legítimo:
        el elemento no es un Bot o no tiene ese stat.

        FIX: la versión anterior usaba "except Exception: return None",
        que se tragaba cualquier error real (p.ej. el AttributeError que
        salía de _stats sin inicializar antes de que Tiene_Stats tuviera
        deserialize_stats) y lo disfrazaba de "no es un bot". Ahora se
        comprueba explícitamente con tiene_stat(), que ya existe para
        esto — así un fallo real sigue reventando en vez de esconderse.
        """
        if not hasattr(elemento, "tiene_stat") or not elemento.tiene_stat("id"):
            return None
        return int(elemento.get_stat("id"))

    async def aplicar_delta_sector(self, mutaciones: list[Mutacion]) -> None:
        """Aplica, en orden y bajo un único lock, todas las mutaciones que un
        Sector devolvió en su TickDelta."""
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
        """Asigna id real (reutilizando el mismo contador que asignar_id) y
        registra el elemento nuevo. Solo debe llamarse ya dentro de self._lock."""
        self._id_counter += 1
        eid = self._id_counter
        m.elemento.id_elemento = eid  # el objeto llega sin id — se le asigna aquí
        self._elements[eid] = m.elemento
        self._registrar_sonidos_de(m.elemento)

        celda = self._gold_cells.setdefault(m.pos, Celda())
        if m.tipo_slot == "suelo":
            celda.suelo = eid
        elif m.tipo_slot == "bot":
            celda.bot = eid
            # FIX: bot_id, no eid (ver _bot_id_de).
            bot_id = self._bot_id_de(m.elemento)
            if bot_id is not None:
                self._bot_positions[bot_id] = m.pos
            else:
                logger.warning(
                    "aplicar_delta_sector: elemento bot en %s sin bot_id "
                    "extraíble — no se indexa en _bot_positions.",
                    m.pos,
                )
        else:
            celda.resto.append(eid)

        logger.debug(
            "Elemento %s creado en %s (marcador_local=%s)",
            eid,
            m.pos,
            m.marcador_local,
        )

    def _aplicar_eliminar_sin_lock(self, m: EliminarElemento) -> None:
        """Solo debe llamarse ya dentro de self._lock."""
        celda = self._gold_cells.get(m.pos)
        if celda is None:
            logger.warning(
                "aplicar_delta_sector: no hay celda en %s para eliminar %s",
                m.pos,
                m.id_elemento,
            )
            return

        elemento = self._elements.get(m.id_elemento)
        if elemento is not None:
            try:
                self._liberar_sonidos_de(elemento)
            except Exception as exc:
                raise ValueError(f"Error eliminando sonidos de {elemento}") from exc

        if celda.suelo == m.id_elemento:
            celda.suelo = None
        elif celda.bot == m.id_elemento:
            celda.bot = None
            # FIX: hay que resolver el bot_id ANTES de hacer pop en
            # self._elements más abajo, o ya no habría forma de recuperar
            # el objeto para extraer su stat "id".
            elemento = self._elements.get(m.id_elemento)
            bot_id = self._bot_id_de(elemento) if elemento is not None else None
            if bot_id is not None:
                self._bot_positions.pop(bot_id, None)
        elif m.id_elemento in celda.resto:
            celda.resto.remove(m.id_elemento)
        else:
            logger.warning(
                "aplicar_delta_sector: elemento %s no encontrado en %s",
                m.id_elemento,
                m.pos,
            )
            return

        self._elements.pop(m.id_elemento, None)
        if celda.suelo is None and celda.bot is None and not celda.resto:
            self._gold_cells.pop(m.pos, None)

    def _aplicar_mover_sin_lock(self, m: MoverElemento) -> None:
        """Mueve un elemento de pos_origen a pos_destino, conservando su id.
        pos_destino puede caer en la región de otro sector: aquí no importa,
        porque _gold_cells es único y global — la noción de "a qué sector
        pertenece" solo existe al construir el siguiente delta de ENTRADA
        (obtener_celdas_en_región ya filtra por región). Solo debe llamarse
        ya dentro de self._lock."""
        celda_origen = self._gold_cells.get(m.pos_origen)
        if celda_origen is None:
            logger.warning(
                "aplicar_delta_sector: no hay celda en %s para mover %s",
                m.pos_origen,
                m.id_elemento,
            )
            return

        tipo_slot = None
        if celda_origen.suelo == m.id_elemento:
            celda_origen.suelo = None
            tipo_slot = "suelo"
        elif celda_origen.bot == m.id_elemento:
            celda_origen.bot = None
            tipo_slot = "bot"
        elif m.id_elemento in celda_origen.resto:
            celda_origen.resto.remove(m.id_elemento)
            tipo_slot = "resto"
        else:
            logger.warning(
                "aplicar_delta_sector: elemento %s no encontrado en %s",
                m.id_elemento,
                m.pos_origen,
            )
            return

        if (
            celda_origen.suelo is None
            and celda_origen.bot is None
            and not celda_origen.resto
        ):
            self._gold_cells.pop(m.pos_origen, None)

        celda_destino = self._gold_cells.setdefault(m.pos_destino, Celda())
        if tipo_slot == "suelo":
            celda_destino.suelo = m.id_elemento
        elif tipo_slot == "bot":
            celda_destino.bot = m.id_elemento
            # FIX: bot_id, no id_elemento — se resuelve a partir del objeto
            # ya guardado en self._elements (todavía no se ha tocado aquí).
            elemento = self._elements.get(m.id_elemento)
            bot_id = self._bot_id_de(elemento) if elemento is not None else None
            if bot_id is not None:
                self._bot_positions[bot_id] = m.pos_destino
        else:
            celda_destino.resto.append(m.id_elemento)

    # ---- Traducción Cell (proto) <-> Celda (interno) ----

    def _slot_bytes_a_id(self, blob: bytes) -> Optional[uint64]:
        # FIX: un blob vacío significa "slot desocupado" (ver comentario en
        # common.proto: "vacío si no hay elemento en este slot"), no un
        # error — antes se lanzaba ValueError aquí, lo cual contradecía el
        # propio _cell_a_celda, que ya filtraba resto con "if eid is not
        # None" dando por hecho (incorrectamente, hasta este fix) que este
        # método podía devolver None.
        if not blob:
            return None
        data = json.loads(blob.decode())
        elemento = reconstruir_elemento(data)
        eid = getattr(elemento, "id_elemento", None)
        if eid is None:
            raise ValueError(
                f"Elemento deserializado sin 'id_elemento' (clase={data.get('__clase__')!r})."
            )
        self._elements[eid] = elemento
        return eid

    def _id_a_slot_bytes(self, eid: Optional[uint64]) -> bytes:
        if eid is None:
            return b""
        elemento = self._elements.get(eid)
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

            self._registrar_sonidos_de(self._elements[eid])

            celda = self._gold_cells.setdefault(pos, Celda())
            if type_id == "suelo":
                celda.suelo = eid
            elif type_id == "bot":
                celda.bot = eid
                elemento = self._elements.get(eid)
                bot_id = self._bot_id_de(elemento) if elemento is not None else None
                if bot_id is not None:
                    self._bot_positions[bot_id] = pos
                else:
                    logger.warning(
                        "crear_elemento: bot en %s sin bot_id extraíble — "
                        "no se indexa en _bot_positions.",
                        pos,
                    )
            else:
                celda.resto.append(eid)

            logger.debug("Elemento %s creado en %s (type_id=%s)", eid, pos, type_id)
            return True, ""

    async def construir_elemento(
        self,
        pos: tuple[int, int],
        nombre_clase: str,
        campos: dict,
    ) -> tuple[bool, str, Optional[uint64]]:
        """
        Crea un elemento NUEVO llamando a su __init__ real (ver
        Core.Entities.Elementos.registry.construir_elemento) -- a diferencia
        de crear_elemento(), que reensambla un elemento ya construido en
        otro proceso (reubicación entre sectores), esto es para cuando algo
        (la consola, una acción del mundo) decide que un elemento empieza a
        existir ahora mismo. El id se asigna aquí, no lo trae 'campos'.
        """
        from Core.Entities.Elementos.registry import construir_elemento

        async with self._lock:
            self._id_counter += 1
            eid = self._id_counter

            # JSON no tiene tuplas: cualquier lista que llegue en 'campos'
            # (casilla, rgb_base...) se asume tupla -- ninguno de los
            # constructores vistos hasta ahora espera una lista de verdad
            # como parámetro. Si algún comportamiento futuro sí necesitara
            # una lista real, esta conversión habría que exceptuarla para
            # ese campo.
            campos_normalizados = {
                k: tuple(v) if isinstance(v, list) else v for k, v in campos.items()
            }

            try:
                elemento = construir_elemento(
                    nombre_clase, id_elemento=eid, **campos_normalizados
                )
            except (ValueError, TypeError) as exc:
                return False, f"No se pudo construir '{nombre_clase}': {exc}", None

            self._elements[eid] = elemento
            self._registrar_sonidos_de(elemento)

            celda = self._gold_cells.setdefault(pos, Celda())
            tipo_slot = elemento.tipo_slot()
            if tipo_slot == "suelo":
                celda.suelo = eid
            elif tipo_slot == "bot":
                celda.bot = eid
            else:
                celda.resto.append(eid)

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
            celda = self._gold_cells.get(pos)
            if celda is None:
                return False, f"No hay celda en {pos}."

            # Comprueba en los tres slots posibles -- antes solo miraba
            # suelo/bot, dejando 'resto' sin poder modificarse nunca.
            if element_id not in (celda.suelo, celda.bot, *celda.resto):
                return False, f"Elemento {element_id} no encontrado en {pos}."

            elemento = self._elements.get(element_id)
            if elemento is None:
                return False, f"Elemento {element_id} no encontrado en _elements."

            elemento.aplicar_patch(patch)
            return True, ""

    async def eliminar_elemento(
        self, pos: tuple[int, int], element_id: uint64
    ) -> tuple[bool, str]:
        async with self._lock:
            celda = self._gold_cells.get(pos)
            if celda is None:
                return False, f"No hay celda en {pos}."

            elemento = self._elements.get(element_id)
            if elemento is not None:
                self._liberar_sonidos_de(elemento)

            if celda.suelo == element_id:
                celda.suelo = None
            elif celda.bot == element_id:
                celda.bot = None
                elemento = self._elements.get(element_id)
                bot_id = self._bot_id_de(elemento) if elemento is not None else None
                if bot_id is not None:
                    self._bot_positions.pop(bot_id, None)
            elif element_id in celda.resto:
                celda.resto.remove(element_id)
            else:
                return False, f"Elemento {element_id} no encontrado en {pos}."

            self._elements.pop(element_id, None)

            if celda.suelo is None and celda.bot is None and not celda.resto:
                self._gold_cells.pop(pos, None)

            return True, ""

    async def eliminar_avatar_bot(self, bot_id: int) -> tuple[bool, str]:

        bot_id = int(bot_id)
        pos = self._bot_positions.get(bot_id)
        if pos is None:
            return False, f"Bot {bot_id!r} no encontrado en bot_positions."

        async with self._lock:
            celda = self._gold_cells.get(pos)
            if celda is None or celda.bot is None:
                return False, f"No hay avatar de bot en {pos}."
            element_id = celda.bot

        return await self.eliminar_elemento(pos, element_id)

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
                "matar_bot: sin gestor_bots_client configurado — el script del bot %s no será terminado.",
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

    # ---- Sonido ------------

    async def obtener_audio(self, id_sonido: str) -> tuple[bool, str, bytes]:
        """
        Sirve el audio completo de un id_sonido ya registrado en el
        CacheAudio de este proceso -- lo pide Unity cuando recibe una
        referencia (id/duracion/vol) en consultar_representacion y no tiene
        ese id cacheado en su lado.

        No usa self._lock: CacheAudio no forma parte del estado mutado por
        aplicar_delta_sector/crear_elemento/etc. (no hay sectores ni
        posiciones involucradas), así que no hay condición de carrera que
        proteger aquí -- registrar() solo añade entradas nuevas, nunca las
        modifica ni las borra.
        """
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
            logger.warning(
                "resolver_accion: acción '%s' no tiene funcion (bot %s)",
                action_type,
                bot_id,
            )
            return ActionResult(
                ok=False,
                error=f"Acción '{action_type}' no ejecutable por Logica_Mundo.",
            )

        ctx = AccionContext(
            bot_id=bot_id,
            payload=payload,
            gold_cells=self._gold_cells,
            elements=self._elements,
            bot_positions=self._bot_positions,
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

        # ---- Elementos globales (ciclo día/noche, lunar, clima...) ----

    async def avanzar_elementos_globales(self, tick_id: int) -> dict:
        cambios: dict = {}
        async with self._lock:
            self._tick_actual = tick_id  # NUEVO: se guarda para que Vista_Foco pueda detectar "tick nuevo"
            for elem in self._elementos_globales.values():
                cambios.update(elem.tick(tick_id))
        return cambios

    async def get_tick_actual(self) -> int:
        async with self._lock:
            return self._tick_actual

    async def get_elementos_globales(self) -> dict[str, dict]:
        """
        Devuelve un snapshot serializable (nombre → dict) de todos los
        elementos globales. Sustituye a GestorMundo.GetGlobalState
        (retirado, ver decisión "elementos_globales: B") — ahora vive
        aquí porque el estado de estos elementos siempre vivió en
        Logica_Mundo, no en Gestor_Mundo.
        """
        async with self._lock:
            return {
                nombre: elem.to_snapshot()
                for nombre, elem in self._elementos_globales.items()
            }

    async def obtener_celdas_en_region(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        excluir_min: Optional[tuple[int, int]] = None,
        excluir_max: Optional[tuple[int, int]] = None,
    ) -> list:
        x0, y0 = min_pos
        x1, y1 = max_pos

        tiene_exclusion = excluir_min is not None and excluir_max is not None
        if tiene_exclusion:
            ex0, ey0 = excluir_min  # type: ignore
            ex1, ey1 = excluir_max  # type: ignore

        async with self._lock:
            resultado = []
            for (x, y), celda in self._gold_cells.items():
                if not (x0 <= x < x1 and y0 <= y < y1):
                    continue
                if tiene_exclusion and (ex0 <= x < ex1 and ey0 <= y < ey1):
                    continue
                resultado.append(self._celda_a_cell((x, y), celda))
            return resultado

    async def actualizar_celdas(self, changed_cells: list) -> None:
        async with self._lock:
            for cell in changed_cells:
                pos = (cell.pos.x, cell.pos.y)
                celda = self._cell_a_celda(cell)
                if celda.suelo is None and celda.bot is None and not celda.resto:
                    self._gold_cells.pop(pos, None)
                else:
                    self._gold_cells[pos] = celda

    async def consultar_representacion(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str],
        modo: str,
        tipos: list[str] | None = None,  # None = sin filtro de tipo
    ) -> bytes:
        x0, y0 = min_pos
        x1, y1 = max_pos

        elementos = []
        suelo_resultado = []
        atmosfera = [] # TODO: representar sistema atmosferico

        async with self._lock:
            for (x, y), celda in self._gold_cells.items():
                if not (x0 <= x < x1 and y0 <= y < y1):
                    continue

                if celda.suelo is not None:
                    suelo_elemento = self._elements.get(celda.suelo)
                    if suelo_elemento is not None and (
                        tipos is None or type(suelo_elemento).__name__ in tipos
                    ):
                        campos = suelo_elemento.representacion(modo, incluir)

                        if campos.get("elemento") or campos.get("comportamientos"):
                            suelo_resultado.append({**campos})

                # bot/resto: igual que antes, solo que ya sin celda.suelo
                # mezclado en la misma lista de ids.
                for eid in (celda.bot, *celda.resto):
                    elemento: Elemento = self._elements.get(eid)
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
            elemento = self._elements.get(element_id)
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
                    for (x, y), celda in self._gold_cells.items()
                },
                "elements": {
                    str(eid): elemento.serializar(modo=Modos.guardado)
                    for eid, elemento in self._elements.items()
                },
                "bot_positions": {
                    bid: list(pos) for bid, pos in self._bot_positions.items()
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
        """
        Mantiene como máximo SNAPSHOT_MAX ficheros en SNAPSHOT_DIR, borrando
        los más antiguos por número de snapshot (no por fecha de disco, para
        no depender de que el reloj/mtime sea fiable). Se llama tras cada
        guardado — así el límite se aplica de forma incremental, sin picos.
        """
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
            self._id_counter = data.get("id_counter", 0)

            self._elements = {
                int(eid): reconstruir_elemento(edata)
                for eid, edata in data.get("elements", {}).items()
            }

            self._gold_cells = {
                tuple(map(int, k.split(","))): Celda(
                    suelo=v["suelo"], bot=v["bot"], resto=v["resto"]
                )
                for k, v in data.get("gold_cells", {}).items()
            }

            self._bot_positions = {
                int(bid): tuple(pos)
                for bid, pos in data.get("bot_positions", {}).items()
            }

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
        # TODO: esto es un parche temporal para tener suelo. hay que hacer un
        # generador de suelo en condiciones
        """
        Crea una instancia de Suelo por cada celda del grid, usando
        Config.settings.ANCHO/ALTO (tamaño del mundo — el mismo en
        local que en AWS, ver topologia.py). Se ejecuta síncronamente
        dentro de __init__: no hace falta await ni self._lock porque
        el objeto todavía no es accesible desde ningún otro sitio en
        este punto (nadie más puede tener una referencia a self aún).

        No usa asignar_id() (que sí es async y sí toma el lock) por el
        mismo motivo — sería tomar un lock que no puede tener
        contención posible todavía, solo overhead sin beneficio.
        """
        # for x in range(config.ANCHO):
        #     for y in range(config.ALTO):
        #         self._id_counter += 1
        #         eid = self._id_counter
        #         suelo = Suelo_Cesped(casilla=(x, y), id_elemento=eid)
        #         self._elements[eid] = suelo
        #         self._gold_cells[(x, y)] = Celda(suelo=eid)

        logger.info(
            "Suelo poblado: %d x %d celdas (%d elementos Suelo creados).",
            config.GRID_WIDTH,
            config.GRID_HEIGHT,
            config.GRID_WIDTH * config.GRID_HEIGHT,
        )
