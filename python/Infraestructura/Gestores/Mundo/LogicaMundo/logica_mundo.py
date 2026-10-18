# Infraestructura/Gestores/Mundo/LogicaMundo/logica_mundo.py

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import math
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any, Optional

from vectors import Vector2

from Config.validacion_simulacion import validar_estabilidad
from Core.Entities.Mundo.Funciones.tipo_slot import tipo_slot_de
from Core.Entities.Mundo.mundo import Mundo
from Core.Entities.Mundo.Atmosfera.celda_atmosfera import Celda_Atmosfera
from Core.Entities.Mundo.Suelo.celda import Celda
from Core.Entities.Elementos.elemento import Elemento
from Core.Entities.Elementos.registry import (
    construir_elemento as construir_desde_registro,
    reconstruir_elemento,
)

from Infraestructura.Gestores.Mundo.Sector.escala_atmosfera import (
    pos_terreno_a_atmosfera,
)
from Infraestructura.Gestores.Transporte import celda_atmosfera_proto
from Infraestructura.Gestores.Transporte.gestor_bots_client_async import (
    GestorBotsClientAsync,
)
from Infraestructura.Gestores.tipos_comunes import ActionResult
import Config.settings as config

logger = logging.getLogger(__name__)


# ---- Generación del mundo ----

# Cada cuántas celdas creadas se cede el control al bucle de eventos. Mundo
# no es seguro entre hilos, así que la generación NO va a un hilo aparte:
# corre en esta misma corrutina y cede cada tanto para que el proceso siga
# respondiendo (Heartbeat, EstadoGeneracionMundo...).
CELDAS_POR_CESION: int = 500

# Claves sin las cuales un snapshot de Logica no se puede restaurar. Se
# comprueban ANTES de tocar nada: así un snapshot incompleto (p. ej. de una
# versión anterior) se rechaza limpio en vez de dejar el mundo a medio restaurar.
_CLAVES_SNAPSHOT_EXIGIDAS = ("atmosfera", "reloj", "tick_actual", "estaciones")

# Clase de suelo con la que se rellena el mundo de prueba. Es el nombre con
# el que está registrada en Core/Entities/Elementos/registry.
TIPO_SUELO_BASE: str = "Suelo_Piedra"


class EstadoGeneracion(IntEnum):
    """Valores numéricos IGUALES a los del enum EstadoGeneracion del .proto
    (NO_INICIADA debe ser 0, el valor por defecto de un enum proto3)."""

    NO_INICIADA = 0
    EN_CURSO = 1
    COMPLETADA = 2
    ERROR = 3


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
        mundo: "Mundo | None" = None,
    ):
        # Falla rápido si dt, tamaño de celda o difusividades vuelven inestable
        # el esquema explícito (ver Config/validacion_simulacion.py).
        validar_estabilidad()
        self.SNAPSHOT_DIR = Path(config.SNAPSHOT_DIR)

        # Todo el estado espacial (celdas de terreno, celdas de atmósfera,
        # elementos por id, posiciones, y la traducción bot_id -> id_elemento)
        # vive en Mundo -- síncrono, sin lock propio. LogicaMundo se queda con
        # lo que no es "grid": el lock async, el contador de ids, snapshots,
        # sonido, eventos globales, ciclo de vida de bots y generación.
        self.mundo: Mundo = mundo or Mundo()

        self._id_counter: int = 100

        self._active_events: dict[str, GlobalEvent] = {}
        self._parches_atmosfera: set[tuple[int, int]] = set()
        self._event_counter: int = 0

        self._elementos_globales: dict[str, ElementoGlobal] = {}
        self._tick_actual: int = 0

        self._gestor_bots_client = gestor_bots_client

        self._lock: asyncio.Lock = asyncio.Lock()

        # Estado de la generación del mundo. Se lee SIN lock (ver
        # estado_generacion): el generador mantiene el lock durante toda la
        # generación y, si el sondeo lo pidiera, se bloquearía hasta el final.
        self._estado_generacion: EstadoGeneracion = EstadoGeneracion.NO_INICIADA
        self._generacion_hechas: int = 0
        self._generacion_total: int = 0
        self._generacion_error: str = ""
        # Referencia a la tarea: asyncio solo guarda referencias débiles y una
        # tarea sin referencia puede ser recogida por el GC a mitad de camino.
        self._tarea_generacion: Optional[asyncio.Task] = None

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

    # ---- Traducción Cell (proto) <-> Celda (interno) ----

    def _slot_bytes_a_id(self, blob: bytes) -> Optional[int]:
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

    def _id_a_slot_bytes(self, eid: Optional[int]) -> bytes:
        if eid is None:
            return b""
        elemento = self.mundo.obtener_elemento(eid)
        if elemento is None:
            logger.warning("_id_a_slot_bytes: elemento %s no encontrado.", eid)
            return b""
        return json.dumps(elemento.serializar()).encode()

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

    def _siguiente_id(self) -> int:
        """Siguiente id de elemento. Síncrono y SIN lock: lo llaman tanto
        asignar_id (que toma el lock) como el generador del mundo (que ya lo
        tiene, y asyncio.Lock no es reentrante)."""
        self._id_counter += 1
        return self._id_counter

    async def asignar_id(self) -> int:
        async with self._lock:
            return self._siguiente_id()

    # ---- Elementos ----

    async def crear_elemento(
        self, pos: tuple[int, int], element: bytes
    ) -> tuple[bool, str]:
        """Añade al mundo un elemento ya construido y serializado. El slot se
        decide por CLASE (tipo_slot_de); ya no hay type_id. Se valida TODO
        antes de registrar nada, para no dejar huérfanos."""
        async with self._lock:
            try:
                elemento = reconstruir_elemento(json.loads(element.decode()))
            except (
                ValueError,
                KeyError,
                TypeError,
            ) as exc:  # JSONDecodeError es ValueError
                return False, f"Elemento inválido: {exc}"

            eid = getattr(elemento, "id_elemento", None)
            if not eid:
                return False, "El elemento no tiene 'id_elemento' asignado."
            if eid in self.mundo.elementos:
                return False, f"Ya existe un elemento con id {eid}."

            slot = tipo_slot_de(elemento)
            bot_id = self._bot_id_de(elemento) if slot == "bot" else None
            if slot == "bot" and bot_id is None:
                logger.warning("crear_elemento: bot en %s sin bot_id extraíble.", pos)
            try:
                self.mundo.crear_elemento(eid, pos, slot, elemento, bot_id=bot_id)
            except ValueError as exc:  # slot ocupado
                return False, str(exc)
            self._registrar_sonidos_de(elemento)  # solo tras crear con éxito
            return True, ""

    def _construir_elemento_sin_lock(
        self, pos: tuple[int, int], nombre_clase: str, campos: dict
    ) -> tuple[bool, str, Optional[int]]:
        """Cuerpo real de construir_elemento. Sin lock: lo llaman construir_elemento
        (que lo toma) y el generador (que ya lo tiene; asyncio.Lock no es reentrante).
        Es síncrono, así que es atómico en el bucle de eventos."""
        eid = self._siguiente_id()
        campos_normalizados = {
            k: tuple(v) if isinstance(v, list) else v for k, v in campos.items()
        }
        try:
            elemento = construir_desde_registro(
                nombre_clase, id_elemento=eid, **campos_normalizados
            )
        except (
            ValueError,
            TypeError,
            KeyError,
        ) as exc:  # KeyError: clase no registrada
            return False, f"No se pudo construir '{nombre_clase}': {exc}", None

        slot = tipo_slot_de(elemento)
        bot_id = self._bot_id_de(elemento) if slot == "bot" else None
        if slot == "bot" and bot_id is None:
            logger.warning("construir_elemento: bot en %s sin bot_id extraíble.", pos)
        try:
            # UNA sola alta (antes se hacía dos veces y la segunda lanzaba ValueError).
            self.mundo.crear_elemento(eid, pos, slot, elemento, bot_id=bot_id)
        except ValueError as exc:  # id duplicado o slot ocupado
            return False, str(exc), None
        self._registrar_sonidos_de(elemento)
        logger.debug(
            "Elemento %s (%s) construido en %s (slot=%s)", eid, nombre_clase, pos, slot
        )
        return True, "", eid

    async def construir_elemento(
        self,
        pos: tuple[int, int],
        nombre_clase: str,
        campos: dict,
    ) -> tuple[bool, str, Optional[int]]:
        """Crea un elemento NUEVO llamando a su __init__ real. Si es un bot,
        se indexa su bot_id (si no, quedaría invisible para
        eliminar_avatar_bot/matar_bot/resolver_accion)."""
        async with self._lock:
            return self._construir_elemento_sin_lock(pos, nombre_clase, campos)

    async def modificar_elemento(
        self, pos: tuple[int, int], element_id: int, patch: dict
    ) -> tuple[bool, str]:
        async with self._lock:
            if not self.mundo.contiene(pos, element_id):
                return False, f"Elemento {element_id} no encontrado en {pos}."

            elemento = self.mundo.obtener_elemento(element_id)
            if elemento is None:
                return False, f"Elemento {element_id} no encontrado en el registro."

            try:
                elemento.aplicar_patch(patch)
            except (ValueError, AttributeError) as exc:
                # Un patch inválido es un error del que llama, no del servidor:
                # se devuelve como (False, msg) en vez de reventar el RPC.
                return False, str(exc)
            return True, ""

    def _eliminar_elemento_sin_lock(
        self, pos: tuple[int, int], element_id: int
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
        self, pos: tuple[int, int], element_id: int
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
        """
        Termina un bot: elimina su avatar Y termina su script.

        Si el avatar ya no está, NO se corta aquí: se termina igualmente el
        script. Es el caso normal, no una rareza: cuando un Sector informa de
        una muerte (dead_bot_ids), actualizar_celdas ya ha aplicado la celda
        sin el avatar y lo ha olvidado; y en el caso "perdido" de un
        movimiento externo, Logica ya lo eliminó. Con el return anticipado
        del original, el script del bot muerto no se terminaba nunca.
        """
        ok, error = await self.eliminar_avatar_bot(bot_id)
        if not ok:
            logger.warning(
                "matar_bot: avatar de %s no eliminado (%s); se termina "
                "igualmente su script.",
                bot_id,
                error,
            )

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

    # ---- Eventos ----

    async def emitir_eventos(self, eventos: list) -> None:
        """
        Emite en el bus del mundo los eventos pedidos por los elementos de los
        Sectores (EventoMundo, en orden). Un payload ilegible PROPAGA (RPC con
        ok=False -> fatal en el Gestor, decisión B1): es un bug, no un caso normal.
        Un suscriptor roto NO debe matar el mundo: el bus lo aísla y lo registra.
        """
        async with self._lock:
            for ev in eventos:
                datos = json.loads(ev.payload.decode())
                self.mundo.bus_eventos.emitir(
                    ev.tipo, *datos["args"], **datos["kwargs"]
                )

    # ---- Sonido ----

    async def obtener_audio(self, id_sonido: str) -> tuple[bool, str, bytes]:
        # FUERA DE ALCANCE: self._cache_audio no existe todavía (esto lanza
        # AttributeError). Decisión tomada: el audio se aborda aparte.
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

        try:
            async with self._lock:
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

    # async def avanzar_elementos_globales(self, tick_id: int) -> dict:
    #     cambios: dict = {}
    #     async with self._lock:
    #         self._tick_actual = tick_id
    #         self.mundo.reloj.next_tick()
    #         for elem in self._elementos_globales.values():
    #             cambios.update(elem.tick(tick_id))
    #     return cambios

    async def avanzar_elementos_globales(self, tick_id: int) -> dict:
        """Ejecuta tick() de cada elemento global y devuelve sus cambios.
        YA NO avanza el tick ni el reloj (eso es avanzar_tick). Con
        _elementos_globales vacío devuelve {} sin hacer nada, así que
        llamarlo es inofensivo; si prefieres saltarlo del todo, basta con
        no llamarlo desde Gestor_Mundo."""
        cambios: dict = {}
        async with self._lock:
            for elem in self._elementos_globales.values():
                cambios.update(elem.tick(tick_id))
        return cambios

    async def avanzar_tick(self, tick_id: int) -> None:
        """Avanza el tiempo del mundo un tick: fija el tick actual y hace
        avanzar el reloj (y con él los ciclos solar/lunar/anual, que son los
        que luego lee obtener_progreso_ciclos).

        Está separado de los elementos globales a propósito: el avance del
        tiempo no depende de que existan elementos globales. Es lo que
        vigila vista_foco (vía tick_actual) para saber que hubo tick nuevo,
        así que debe llamarse una vez por tick, aunque no haya ninguno."""
        async with self._lock:
            self._tick_actual = tick_id
            self.mundo.reloj.next_tick()

    async def get_tick_actual(self) -> int:
        async with self._lock:
            return self._tick_actual

    async def get_elementos_globales(self) -> dict[str, dict]:
        async with self._lock:
            return {
                nombre: elem.to_snapshot()
                for nombre, elem in self._elementos_globales.items()
            }

    # ---- Generación del mundo ----
    #
    # Flujo: el RPC GenerarMundo llama a generar_mundo(), que lanza la
    # generación en segundo plano y vuelve al instante; el cliente sondea
    # EstadoGeneracionMundo (estado_generacion()) hasta COMPLETADA o ERROR.
    #
    # Orden: primero la malla de atmósfera, luego el Suelo. Si algo falla se
    # corta TODO (estado ERROR); no hay reintento ni rollback (ver
    # generar_mundo).

    async def generar_mundo(self) -> tuple[bool, str]:
        """Inicia la generación y vuelve. Por ahora SIEMPRE genera (decisión
        del usuario: no mezclar la política de arranque con la generación),
        con una sola excepción: si ya hay una en curso se rechaza, porque dos
        generaciones seguidas bajo el mismo lock duplicarían el mundo.

        AVISO: no limpia el mundo previo. Está pensada para llamarse sobre un
        mundo VACÍO (arranque limpio); llamarla sobre uno ya generado o a
        medias sobrescribiría la atmósfera y duplicaría/pisaría los suelos."""
        if self._estado_generacion == EstadoGeneracion.EN_CURSO:
            return False, "Ya hay una generación del mundo en curso."
        # Se marca EN_CURSO ANTES de crear la tarea y sin ningún await de por
        # medio: dos llamadas simultáneas no pueden pasar ambas la
        # comprobación de arriba.
        self._estado_generacion = EstadoGeneracion.EN_CURSO
        self._generacion_hechas = 0
        self._generacion_total = 0
        self._generacion_error = ""
        self._tarea_generacion = asyncio.create_task(
            self._generar_mundo_en_segundo_plano(), name="generar_mundo"
        )
        return True, ""

    def estado_generacion(self) -> tuple[EstadoGeneracion, float, str]:
        """(estado, progreso 0.0-1.0, mensaje de error). Síncrono y SIN lock a
        propósito: el generador mantiene el lock durante toda la generación,
        así que si esto lo pidiera el sondeo no obtendría respuesta hasta el
        final, que es justo cuando ya no hace falta."""
        total = self._generacion_total
        progreso = self._generacion_hechas / total if total > 0 else 0.0
        if self._estado_generacion == EstadoGeneracion.COMPLETADA:
            progreso = 1.0
        return self._estado_generacion, progreso, self._generacion_error

    async def apagar(self) -> None:
        """Cancela la generación en curso. logica_mundo_server debe llamarlo
        antes de server.stop y cerrar gestor_bots_client DESPUÉS de server.stop."""
        tarea = self._tarea_generacion
        if tarea is not None and not tarea.done():
            tarea.cancel()
            await asyncio.gather(tarea, return_exceptions=True)

    async def _generar_mundo_en_segundo_plano(self) -> None:
        try:
            # El lock se mantiene TODO el rato: nadie puede leer ni modificar
            # el mundo a medio generar. A cambio, cualquier otro RPC que
            # necesite el lock espera a que termine (incluido el tick de
            # Gestor_Mundo: por eso debe arrancar congelado).
            async with self._lock:
                await self._generar_mundo_bajo_lock()
        except asyncio.CancelledError:
            self._generacion_error = "Generación cancelada (apagado)."
            self._estado_generacion = EstadoGeneracion.ERROR
            raise
        except Exception as exc:
            logger.exception("Generación del mundo fallida; se corta todo.")
            self._generacion_error = f"{type(exc).__name__}: {exc}"
            self._estado_generacion = EstadoGeneracion.ERROR
        else:
            self._estado_generacion = EstadoGeneracion.COMPLETADA
            logger.info("Mundo generado (%d celdas creadas).", self._generacion_hechas)

    async def _avanzar_generacion(self) -> None:
        """Cuenta una celda creada y, cada CELDAS_POR_CESION, cede el control
        al bucle de eventos (sin soltar el lock)."""
        self._generacion_hechas += 1
        if self._generacion_hechas % CELDAS_POR_CESION == 0:
            await asyncio.sleep(0)

    async def _generar_mundo_bajo_lock(self) -> None:
        """Debe llamarse con self._lock YA tomado."""
        # math.ceil: si el mapa no fuera múltiplo de ATMOSFERA_ESCALA, la
        # última fila/columna de casillas seguiría teniendo celda de atmósfera.
        columnas_atm = math.ceil(config.GRID_WIDTH / config.ATMOSFERA_ESCALA)
        filas_atm = math.ceil(config.GRID_HEIGHT / config.ATMOSFERA_ESCALA)
        casillas = config.GRID_WIDTH * config.GRID_HEIGHT
        self._generacion_total = columnas_atm * filas_atm + casillas
        self._generacion_hechas = 0

        # 1) Malla de atmósfera. Viento sin dirección ni fuerza por defecto
        #    (Vector2(0, 0)); una instancia NUEVA por celda para no compartir
        #    un objeto mutable entre todas.
        for ax in range(columnas_atm):
            for ay in range(filas_atm):
                self.mundo.crear_atmosfera((ax, ay), Vector2(0, 0))
                await self._avanzar_generacion()

        # 2) Suelo. Su casilla es su posición (x, y). Se construye por NOMBRE
        #    con argumentos con nombre: Suelo_Piedra(id_elemento, casilla) y
        #    Suelo_Barro(casilla, id_elemento) no comparten orden.
        for x in range(config.GRID_WIDTH):
            for y in range(config.GRID_HEIGHT):
                pos = (x, y)
                ok, error, _ = self._construir_elemento_sin_lock(
                    pos, TIPO_SUELO_BASE, {"casilla": pos}
                )
                if not ok:
                    raise RuntimeError(
                        f"No se pudo crear {TIPO_SUELO_BASE} en {pos}: {error}"
                    )
                await self._avanzar_generacion()

    @staticmethod
    def _pos_atmosfera(pos_suelo: tuple[int, int]) -> tuple[int, int]:
        """Posición de TERRENO -> posición en espacio de atmósfera. Una única
        fórmula (la del Sector): si Logica y los Sectores discreparan, la celda
        espejo que lee Unity no sería la que simula el Sector."""
        return pos_terreno_a_atmosfera(
            pos_suelo[0], pos_suelo[1], config.ATMOSFERA_ESCALA
        )

    # ---- Atmósfera (una sola definición de cada método) ----
    #
    # OJO con el espacio de coordenadas: crear_atmosfera recibe la posición
    # EN ESPACIO DE ATMÓSFERA, mientras que obtener_atmosfera y
    # actualizar_atmosfera reciben la del SUELO y la convierten.

    async def crear_atmosfera(
        self, pos_atmosfera: tuple[int, int], viento_objetivo: Any
    ) -> tuple[bool, str]:
        async with self._lock:
            if self.mundo.obtener_atmosfera(pos_atmosfera) is not None:
                logger.warning(
                    "crear_atmosfera: ya existía %s -- se sobrescribe.", pos_atmosfera
                )
            self.mundo.crear_atmosfera(pos_atmosfera, viento_objetivo)
            return True, ""

    async def obtener_atmosfera(
        self, pos_suelo: tuple[int, int]
    ) -> tuple[bool, str, Optional[Celda_Atmosfera]]:
        pos_atmosfera = self._pos_atmosfera(pos_suelo)
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
        pos_atmosfera = self._pos_atmosfera(pos_suelo)
        async with self._lock:
            celda = self.mundo.obtener_atmosfera(pos_atmosfera)
            if celda is None:
                return (
                    False,
                    f"No hay celda de atmósfera para {pos_suelo} (bloque {pos_atmosfera}).",
                )
            try:
                celda.aplicar_patch(patch)
            except ValueError as exc:
                return False, str(exc)
            # Pendiente de entrega al Sector en la fase 0 del próximo tick.
            self._parches_atmosfera.add(pos_atmosfera)
            return True, ""

    async def tomar_parches_atmosfera(self) -> list:
        """Celdas de atmósfera parcheadas desde el último tick, como
        AtmosphereCell, y VACÍA la lista de pendientes. El Gestor las reparte
        a los Sectores en la fase 0. Si la entrega falla es fatal, así que no
        hace falta reencolar: el valor ya está en el gold y en el snapshot."""
        async with self._lock:
            posiciones = sorted(self._parches_atmosfera)
            self._parches_atmosfera.clear()
            return [
                celda_atmosfera_proto.a_proto(self.mundo.malla_atmosfera[p])
                for p in posiciones
                if p in self.mundo.malla_atmosfera
            ]

    async def obtener_celdas_atmosfera_en_region(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        excluir_min: Optional[tuple[int, int]] = None,
        excluir_max: Optional[tuple[int, int]] = None,
    ) -> list:
        """Espejo de obtener_celdas_en_region, para atmósfera -- lo usa
        Gestor_Mundo._calcular_ghost_zone_atmosfera para construir el
        ghost-zone de atmósfera de cada Sector. min_pos/max_pos ya están
        en espacio de atmósfera."""
        async with self._lock:
            return [
                celda_atmosfera_proto.a_proto(celda)
                for _, celda in self.mundo.celdas_atmosfera_en_region(
                    min_pos, max_pos, excluir_min, excluir_max
                )
            ]

    async def actualizar_celdas_atmosfera(self, changed_atmosphere_cells: list) -> None:
        """
        Espejo de la atmósfera simulada por los Sectores. Copia sobre las
        Celda_Atmosfera YA EXISTENTES (no las sustituye): radiación,
        temperatura (K), presión (Pa), viento, humedades y, ESPEJADOS,
        resistencia_viento y bloqueo_total_viento. Estos dos los calcula el
        Sector desde sus cachés; Logica no mantiene cachés propias (decisión
        1-A), así que se copian tal cual y las cachés internas de esta malla
        quedan vacías.
        """
        async with self._lock:
            for cell in changed_atmosphere_cells:
                pos = (cell.pos.x, cell.pos.y)
                celda = self.mundo.malla_atmosfera.get(pos)
                if celda is None:
                    logger.warning(
                        "actualizar_celdas_atmosfera: no existe Celda_Atmosfera "
                        "en %s -- se ignora (¿el mundo no se ha generado?).",
                        pos,
                    )
                    continue

                celda_atmosfera_proto.aplicar_estado_simulado(cell, celda)
                # Espejo (decisión 1-A): se copian, no se recalculan.
                celda_atmosfera_proto.aplicar_espejo_terreno(cell, celda)

    async def obtener_progreso_ciclos(self) -> tuple[float, float, float]:
        """Progreso (0.0-1.0) de los ciclos solar, lunar y anual, para que
        GestorMundo se lo mande a cada Sector en la Fase 0."""
        async with self._lock:
            return (
                self.mundo.ciclo_solar.ciclo.progreso,
                self.mundo.ciclo_lunar.ciclo.progreso,
                self.mundo.ciclo_anual.ciclo.progreso,
            )

    # ---- Región / representación ----

    async def obtener_bots_en_region(
        self, min_pos: tuple[int, int], max_pos: tuple[int, int]
    ) -> list[tuple[int, int, tuple[int, int]]]:
        """[(bot_id, id_elemento, pos)] de los bots cuyo avatar cae en
        [min_pos, max_pos). Logica es el gold de bots y posiciones
        (mundo.bots + mundo.ids); el gestor lo usa para que Sector.load_state
        reponga _bots y _elemento_a_bot tras cada LoadState."""
        x0, y0 = min_pos
        x1, y1 = max_pos
        async with self._lock:
            resultado = []
            for bot_id, eid in self.mundo.bots.items():
                pos = self.mundo.obtener_posicion(eid)
                if pos is not None and x0 <= pos[0] < x1 and y0 <= pos[1] < y1:
                    resultado.append((bot_id, eid, pos))
            return resultado

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
        """
        Aplica el resultado de un tick: sustituye cada celda cambiada por la
        que envía el Sector. Un elemento que cruzó de sector llega como "ya no
        está en la celda origen" + "aparece en la celda destino" (ambas en la
        lista): como su id sigue indexado en mundo.ids, no se da de baja.
        """
        async with self._lock:
            salientes: set = set()
            for cell in changed_cells:
                pos = (cell.pos.x, cell.pos.y)
                salientes |= self.mundo.actualizar_celda(pos, self._cell_a_celda(cell))

            for eid in salientes:
                if eid in self.mundo.ids:
                    continue
                elemento = self.mundo.obtener_elemento(eid)
                if elemento is None:
                    continue
                self._liberar_sonidos_de(elemento)
                self.mundo.olvidar_elemento(eid, bot_id=self._bot_id_de(elemento))

    async def consultar_representar(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str] | None,
        tipos: list[str] | None = None,
    ) -> bytes:
        """
        Representación (lo que ve Unity) de todo lo que hay en el
        rectángulo [min_pos, max_pos).

        `incluir`: None o [] = todo; si no, nombres de clase (de
        Elemento o de comportamientos) a incluir. OJO: desde el proto un
        campo 'repeated' sin enviar llega como [], así que el handler debe
        convertirlo (list(request.incluir) or None) antes de llamar aquí.
        El suelo ignora `incluir` a propósito (ver Suelo.representar).

        """
        x0, y0 = min_pos
        x1, y1 = max_pos

        elementos = []
        suelo_resultado = []
        atmosfera = None

        # TODO(rendimiento): recorre TODA la malla en cada consulta y con el
        # lock tomado (O(mundo) por llamada). Mundo.celdas_en_region ya
        # existe y filtra por rectángulo; comprobar que su semántica de
        # límites coincide (x0 <= x < x1) antes de sustituirlo.
        async with self._lock:
            for (x, y), celda in self.mundo.malla_terreno.items():
                if not (x0 <= x < x1 and y0 <= y < y1):
                    continue

                if celda.suelo is not None:
                    suelo_elemento = self.mundo.obtener_elemento(celda.suelo)
                    if suelo_elemento is not None and (
                        tipos is None or type(suelo_elemento).__name__ in tipos
                    ):
                        campos = self._representar(suelo_elemento, incluir)
                        if campos.get("elemento") or campos.get("comportamientos"):
                            suelo_resultado.append(campos)

                # celda.bot puede ser None: obtener_elemento(None) devuelve
                # None y el 'continue' de abajo lo descarta.
                for eid in (celda.bot, *celda.resto):
                    elemento: Elemento = self.mundo.obtener_elemento(eid)
                    if elemento is None:
                        continue
                    if tipos is not None and type(elemento).__name__ not in tipos:
                        continue
                    campos = self._representar(elemento, incluir)

                    if not campos.get("elemento") and not campos.get("comportamientos"):
                        continue
                    elementos.append(campos)

            # Atmósfera: SOLO la celda que cubre el CENTRO del foco pedido (no
            # todas las del rectángulo). Con tamaño par, // toma la casilla
            # central superior. Es la copia espejo de Logica: refleja el final
            # del último tick completado. Si el centro cae fuera del mundo,
            # queda vacía.
            centro = ((x0 + x1) // 2, (y0 + y1) // 2)
            celda_atm = self.mundo.obtener_atmosfera(self._pos_atmosfera(centro))
            if celda_atm is not None:
                atmosfera = celda_atm.representar()

            return json.dumps(
                {
                    "elementos": elementos,
                    "suelo": suelo_resultado,
                    "atmosfera": atmosfera,
                }
            ).encode()

    async def obtener_elemento(
        self,
        element_id: int,
        tipo_datos: str = "representar",
        incluir: list[str] | None = None,
    ) -> tuple[bool, str, bytes]:
        async with self._lock:
            elemento = self.mundo.obtener_elemento(element_id)
            if elemento is None:
                return False, f"Elemento {element_id} no encontrado.", b""

            if tipo_datos == "serializar":
                # Siempre completo: serializar() no recibe `incluir`.
                datos = elemento.serializar()
            elif tipo_datos == "representar":
                # Antes: incluir or [] (None -> "nada"). Ahora se pasa tal
                # cual: None = todo.
                datos = self._representar(elemento, incluir)
            else:
                return (
                    False,
                    f"tipo_datos desconocido: '{tipo_datos}' "
                    "(usa 'representar' o 'serializar').",
                    b"",
                )

        return True, "", json.dumps(datos, ensure_ascii=False).encode()

    # ---- Atmósfera <-> dict (snapshots) ----
    # Se guarda el estado simulado Y los dos campos espejados (resistencia y
    # bloqueo de viento), porque las ghost zones los leen de aquí (decisión 1-A).
    # Las cachés de Suelo no se guardan: el Sector las reconstruye desde el terreno.
    #
    # NOTA (pendiente 6, opción A): este dict es el ÚNICO formato de snapshot y
    # vive aquí a propósito. Un campo nuevo de Celda_Atmosfera que deba
    # persistir (p. ej. temperatura_suelo) hay que añadirlo en estas dos
    # funciones Y, si también viaja por proto, en celda_atmosfera_proto.

    @staticmethod
    def _atmosfera_a_dict(celda: Celda_Atmosfera) -> dict:
        return {
            "viento_objetivo": [celda.viento_objetivo.x, celda.viento_objetivo.y],
            "radiacion": celda.radiacion,
            "temperatura": celda.temperatura.valor,  # K, AIRE
            "temperatura_suelo": celda.temperatura.valor_suelo,  # K, SUELO
            "presion": celda.presion.valor,  # Pa
            "viento_intensidad": celda.viento.intensidad,
            "viento_direccion": [celda.viento.direccion.x, celda.viento.direccion.y],
            "humedad_absoluta": celda.humedad_absoluta.valor,
            "humedad_relativa": celda.humedad_relativa.valor,
            "resistencia_viento": celda.resistencia_viento,
            "bloqueo_total_viento": celda.bloqueo_total_viento,
        }

    @staticmethod
    def _atmosfera_desde_dict(pos: tuple[int, int], d: dict) -> Celda_Atmosfera:
        celda = Celda_Atmosfera(
            posicion=pos,
            viento_objetivo=Vector2(*d["viento_objetivo"]),
        )
        celda.radiacion = d["radiacion"]
        celda.temperatura.valor = d["temperatura"]
        celda.temperatura.valor_suelo = d["temperatura_suelo"]
        celda.presion.valor = d["presion"]
        celda.viento.intensidad = d["viento_intensidad"]
        celda.viento.direccion = Vector2(*d["viento_direccion"])
        celda.humedad_absoluta.valor = d["humedad_absoluta"]
        celda.humedad_relativa.valor = d["humedad_relativa"]
        celda.resistencia_viento = d["resistencia_viento"]
        celda.bloqueo_total_viento = d["bloqueo_total_viento"]
        return celda

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
                    str(eid): elemento.serializar()
                    for eid, elemento in self.mundo.elementos.items()
                },
                # Se deriva de ids+bots -- no existe un dict propio de
                # posiciones de bot.
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
                "tick_actual": int(self._tick_actual),
                "reloj": self.mundo.reloj.volcar_estado(),
                "estaciones": self.mundo.estaciones.serializar(),
                "atmosfera": {
                    f"{x},{y}": self._atmosfera_a_dict(celda)
                    for (x, y), celda in self.mundo.malla_atmosfera.items()
                },
            }

        # Escritura atómica: se escribe en un temporal y se renombra. Si el
        # proceso muere a mitad, queda el snapshot anterior intacto en vez de
        # un JSON truncado (el .tmp no coincide con el patrón *.json).
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False))
        tmp.replace(path)
        logger.info("Snapshot de Logica_Mundo guardado: %s", path)
        self._purgar_snapshots_antiguos()

    def _purgar_snapshots_antiguos(self) -> None:
        snapshots = sorted(
            self.SNAPSHOT_DIR.glob("logica_mundo_*.json"),
            key=lambda p: p.stem.removeprefix("logica_mundo_"),
        )
        # max(0, ...): sin él, con menos snapshots que SNAPSHOT_MAX el valor
        # es negativo y snapshots[:negativo] BORRABA los más antiguos (con 15
        # snapshots y SNAPSHOT_MAX=20 se borraban 10).
        sobrantes = max(0, len(snapshots) - config.SNAPSHOT_MAX)
        for path in snapshots[:sobrantes]:
            path.unlink(missing_ok=True)
            logger.debug("Snapshot antiguo purgado: %s", path)

    async def load_state(self, snapshot_id: str) -> tuple[bool, str]:
        path = self.SNAPSHOT_DIR / f"logica_mundo_{snapshot_id}.json"
        if not path.exists():
            msg = f"Snapshot '{snapshot_id}' no encontrado en {path}."
            logger.error(msg)
            return False, msg

        data = json.loads(path.read_text())
        faltan = [k for k in _CLAVES_SNAPSHOT_EXIGIDAS if k not in data]
        if faltan:
            msg = f"Snapshot '{snapshot_id}' incompleto: faltan {faltan}."
            logger.error(msg)
            return False, msg

        async with self._lock:
            self.mundo.reloj.restaurar_estado(data["reloj"])
            self.mundo.estaciones.deserializar(data["estaciones"], self.mundo)
            self._tick_actual = int(data["tick_actual"])
            self.mundo.malla_atmosfera = {
                tuple(map(int, k.split(","))): self._atmosfera_desde_dict(
                    tuple(map(int, k.split(","))), v
                )
                for k, v in data["atmosfera"].items()
            }

            self._id_counter = int(data.get("id_counter", 0))

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
        return True, ""

    @staticmethod
    def _representar(elemento, incluir: list[str] | None) -> dict:
        """Llama a elemento.representar() y falla alto si algún eslabón de
        la cadena super() la cortó (devuelve None en vez del dict). Sin
        esto el error sale lejos, como un AttributeError sobre NoneType, y
        no dice qué clase es la culpable."""
        campos = elemento.representar(incluir)
        if campos is None:
            raise TypeError(
                f"{type(elemento).__name__}.representar() devolvió None: "
                "¿alguna clase de su cadena no llama a super().representar()?"
            )
        return campos
