# Infraestructura/Gestores/Mundo/Gestor_Mundo/gestor_mundo.py


import asyncio
import datetime
import json
import logging
import math
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional

import grpc

from Config.settings import (
    ATMOSFERA_ESCALA,
    DEEP_SAVE_INTERVAL_TICKS,
    FALLOS_CONSECUTIVOS_SECTOR_CAIDO,
    GESTOR_BOTS_ADDRESS,
    GRID_HEIGHT,
    GRID_WIDTH,
    MAX_SOUND_DISTANCE,
    MAX_VISION_DISTANCE,
    SECTOR_BASE_PORT,
    SECTOR_HOST,
    SECTOR_SIZE,
    SNAPSHOT_DIR,
    SNAPSHOT_INTERVAL_TICKS,
    SNAPSHOT_MAX,
    SOUND_MAP_CELL_SIZE,
    TICK_TIMEOUT_MS,
    TICKS_PROCESADOS_SEGUNDO,
)
from Infraestructura.Gestores.Mundo.Sector.sector_mode import SectorMode
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2_grpc as sector_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2_grpc as bots_grpc,
)

from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2 as bots_pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as sector_pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

logger = logging.getLogger(__name__)


class ErrorFatal(RuntimeError):
    """Tras esto el proceso DEBE apagarse: seguir dejaría la simulación
    divergiendo en silencio. Nadie la captura salvo para escalarla."""


class ErrorCargaSector(ErrorFatal):
    """Un sector no pudo cargar su estado (gRPC, LoadState ok=False...)."""


class ErrorSincronizacion(ErrorFatal):
    """Un Sector no completó o no entregó el tick (StartTick o GetDelta
    fallido, timeout), o Logica_Mundo no pudo aplicar el delta.
    Los Sectores pueden tener cambios que Logica (el gold) no tiene.
    """


class SystemState(Enum):
    RUNNING = auto()
    PAUSING = auto()
    PAUSED = auto()
    RESUMING = auto()


@dataclass
class SectorInfo:
    """Metadata de un sector conocido por el Gestor_Mundo."""

    col: int
    row: int
    address: str
    mode: SectorMode = SectorMode.INACTIVO
    channel: Optional[grpc.aio.Channel] = field(default=None, repr=False)
    stub: Optional[object] = field(default=None, repr=False)
    ticks_sin_actividad: int = 0  # para anti-thrashing
    fallos_consecutivos: int = 0


class GestorMundo:

    def __init__(self, logica_client):
        self.COLS = math.ceil(GRID_WIDTH / SECTOR_SIZE)
        self.ROWS = math.ceil(GRID_HEIGHT / SECTOR_SIZE)

        self._sectores: dict[tuple[int, int], SectorInfo] = {}

        self._logica_client = logica_client

        self._tick_id: int = 0
        self._snapshot_id: str = ""

        self._state: SystemState = SystemState.RUNNING
        self._modo_paso: bool = False
        self._step_event: asyncio.Event = asyncio.Event()
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()
        self._tick_rate: int = TICKS_PROCESADOS_SEGUNDO
        self._tick_interval: float = self._calcular_intervalo(self._tick_rate)
        self.fatal_event: asyncio.Event = asyncio.Event()
        self.error_fatal: Optional[ErrorFatal] = None
        self._tick_lock: asyncio.Lock = asyncio.Lock()

        self._bots_channel: Optional[grpc.aio.Channel] = None
        self._bots_stub = None

        self._consolidacion_lock: asyncio.Lock = asyncio.Lock()

        self._pending_sounds = {}

        self._modos_previos_freeze: dict[tuple[int, int], SectorMode] = {}

        self._tareas_fondo: set[asyncio.Task] = set()

    def _delta_tiene_actividad(self, delta) -> bool:
        return bool(
            delta.changed_cells
            or delta.movimientos_salientes
            or delta.emitted_sounds
            or delta.dead_bot_ids
        )

    async def start(self, fresh: bool = False) -> None:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

        self._bots_channel = grpc.aio.insecure_channel(GESTOR_BOTS_ADDRESS)
        self._bots_stub = bots_grpc.GestorBotsServiceStub(self._bots_channel)

        if fresh:
            await self._init_fresh()
        else:
            await self._restore_from_snapshot()

        logger.info(
            "GestorMundo arrancado. Sectores: %d. Tick: %d. Snapshot: %s",
            len(self._sectores),
            self._tick_id,
            self._snapshot_id,
        )

    async def _init_fresh(self) -> None:
        """Arranque limpio: conecta todos los sectores, les carga el estado
        gold que tenga Logica (la generación del mundo debe haber terminado
        antes) y los activa."""
        logger.info("Inicio limpio. Creando %d×%d sectores.", self.COLS, self.ROWS)
        for col in range(self.COLS):
            for row in range(self.ROWS):
                info = SectorInfo(
                    col=col, row=row, address=self._sector_address(col, row)
                )
                self._sectores[(col, row)] = info
                await self._connect_sector(info)
        await self._distribute_gold_to_sectors()
        await self._activar_todos()

    async def _restore_from_snapshot(self) -> None:
        snapshot_path = self._latest_snapshot_path()
        if snapshot_path is None:
            logger.warning("No se encontró snapshot. Iniciando limpio.")
            await self._init_fresh()
            return

        logger.info("Restaurando desde %s", snapshot_path)
        data = json.loads(snapshot_path.read_text())
        self._tick_id = data["tick_id"]
        self._snapshot_id = data["snapshot_id"]

        for s in data["sectores"]:
            info = SectorInfo(col=s["col"], row=s["row"], address=s["address"])
            self._sectores[(info.col, info.row)] = info
            await self._connect_sector(info)

        await self._logica_client.load_state(self._snapshot_id)
        await self._distribute_gold_to_sectors()
        # El "mode" guardado en el snapshot se IGNORA a propósito:
        # la hibernación está deshabilitada y todos arrancan ACTIVO.
        await self._activar_todos()

    async def _activar_todos(self) -> None:
        """_set_sector_mode solo loguea si falla: un sector que no pasa a
        ACTIVO no ticaría nunca y nadie se enteraría. Aquí se comprueba."""
        await asyncio.gather(
            *(
                self._set_sector_mode(i, SectorMode.ACTIVO)
                for i in self._sectores.values()
            )
        )
        no_activos = [
            (i.col, i.row)
            for i in self._sectores.values()
            if i.mode != SectorMode.ACTIVO
        ]
        if no_activos:
            raise ErrorCargaSector(f"Sectores que no pasaron a ACTIVO: {no_activos}")

    async def _activar_sector(self, info: SectorInfo) -> None:

        if info.mode == SectorMode.ACTIVO:
            return
        if info.mode == SectorMode.INACTIVO:
            await self._load_sector_state(info)
        # Sin resetear esto, un sector que llevaba mucho tiempo sin actividad
        # volvería a DORMIDO en cuanto acabase este mismo tick.
        info.ticks_sin_actividad = 0
        await self._set_sector_mode(info, SectorMode.ACTIVO)

    async def run_loop(self) -> None:
        while True:
            await self._pause_event.wait()

            if self._modo_paso:
                await self._step_event.wait()
                self._step_event.clear()

            t0 = time.monotonic()
            try:
                async with self._tick_lock:
                    await self._run_tick()
            except ErrorFatal:
                raise  # NO se captura: sube y el proceso muere con código != 0
            except Exception:
                logger.exception("Tick %d abortado por excepción.", self._tick_id)
            elapsed = time.monotonic() - t0

            self._tick_id += 1

            if self._tick_id % SNAPSHOT_INTERVAL_TICKS == 0:
                self._lanzar_en_segundo_plano(self._save_snapshot())

            if self._tick_id % DEEP_SAVE_INTERVAL_TICKS == 0:
                await self._deep_save()

            logger.debug("Tick %d completado en %.3fs", self._tick_id, elapsed)
            if self._tick_interval > 0:
                sobrante = self._tick_interval - elapsed
                if sobrante > 0:
                    await asyncio.sleep(sobrante)

    def _escalar_fatal(self, exc: ErrorFatal) -> None:
        """Para caminos fuera de run_loop (resume() desde el servicer, tareas
        de fondo): ahí una excepción no mata el proceso, así que se avisa."""
        if self.error_fatal is None:
            self.error_fatal = exc
            logger.critical("ERROR FATAL: %r", exc)
        self.fatal_event.set()

    async def _run_tick(self) -> None:
        await self._fase_0()
        await self._fase_1()
        await self._fase_2()

    async def _fase_0(self) -> None:
        activos_y_dormidos = [
            s
            for s in self._sectores.values()
            if s.mode in (SectorMode.ACTIVO, SectorMode.DORMIDO)
        ]

        (
            progreso_solar,
            progreso_lunar,
            progreso_anual,
        ) = await self._logica_client.obtener_progreso_ciclos()

        tareas = []
        for sector in activos_y_dormidos:
            tareas.append(self._enviar_ghost_zone(sector))
            tareas.append(self._enviar_sonidos(sector))
            tareas.append(self._enviar_ghost_zone_atmosfera(sector))
            tareas.append(
                self._enviar_ciclos_globales(
                    sector, progreso_solar, progreso_lunar, progreso_anual
                )
            )

        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        # return_exceptions=True evita que un fallo cancele el resto de tareas,
        # pero deja las excepciones como valores: hay que mirarlas a mano o se pierden.
        for r in resultados:
            if isinstance(r, Exception):
                logger.error("Fallo en _fase_0: %r", r)

    async def _enviar_ghost_zone(self, sector: SectorInfo) -> None:
        ghost_cells = await self._calcular_ghost_zone(sector)

        req = sector_pb.SetGhostZoneRequest(
            tick_id=self._tick_id,
            ghost_cells=ghost_cells,
        )
        try:
            resp = await sector.stub.SetGhostZone(req)
            if not resp.ok:
                logger.warning(
                    "SetGhostZone falló en (%d,%d): %s",
                    sector.col,
                    sector.row,
                    resp.error,
                )
        except grpc.aio.AioRpcError as e:
            logger.error(
                "gRPC error SetGhostZone (%d,%d): %s", sector.col, sector.row, e
            )

    async def _enviar_ghost_zone_atmosfera(self, sector: SectorInfo) -> None:

        ghost_cells = await self._calcular_ghost_zone_atmosfera(sector)
        req = sector_pb.SetAtmosphereGhostZoneRequest(  # type: ignore
            tick_id=self._tick_id,
            ghost_cells=ghost_cells,
        )
        try:
            resp = await sector.stub.SetAtmosphereGhostZone(req)  # type: ignore
            if not resp.ok:
                logger.warning(
                    "SetAtmosphereGhostZone falló en (%d,%d): %s",
                    sector.col,
                    sector.row,
                    resp.error,
                )
        except grpc.aio.AioRpcError as e:
            logger.error(
                "gRPC error SetAtmosphereGhostZone (%d,%d): %s",
                sector.col,
                sector.row,
                e,
            )

    async def _enviar_ciclos_globales(
        self,
        sector: SectorInfo,
        progreso_solar: float,
        progreso_lunar: float,
        progreso_anual: float,
    ) -> None:
        """Manda el progreso (mismo para todos los sectores) de los
        ciclos solar/lunar/anual -- ver Sector.set_ciclos_globales."""
        req = sector_pb.SetGlobalCyclesRequest(  # type: ignore
            tick_id=self._tick_id,
            progreso_solar=progreso_solar,
            progreso_lunar=progreso_lunar,
            progreso_anual=progreso_anual,
        )
        try:
            resp = await sector.stub.SetGlobalCycles(req)  # type: ignore
            if not resp.ok:
                logger.warning(
                    "SetGlobalCycles falló en (%d,%d): %s",
                    sector.col,
                    sector.row,
                    resp.error,
                )
        except grpc.aio.AioRpcError as e:
            logger.error(
                "gRPC error SetGlobalCycles (%d,%d): %s", sector.col, sector.row, e
            )

    async def _enviar_sonidos(self, sector: SectorInfo) -> None:
        sounds = self._pending_sounds.get((sector.col, sector.row), [])
        if not sounds:
            return
        req = sector_pb.SetSoundsRequest(  # type: ignore
            tick_id=self._tick_id,
            sounds=sounds,
        )
        try:
            resp = await sector.stub.SetSounds(req)  # type: ignore
            if not resp.ok:
                logger.warning(
                    "SetSounds falló en (%d,%d): %s", sector.col, sector.row, resp.error
                )
        except grpc.aio.AioRpcError as e:
            logger.error("gRPC error SetSounds (%d,%d): %s", sector.col, sector.row, e)

    async def _fase_1(self) -> None:
        """Ordena a todos los sectores ACTIVOS que computen en paralelo.
        CUALQUIER fallo (excepción gRPC, ok=False, timeout) es fatal: el
        Sector pudo aplicar cambios a su copia que Logica nunca recibirá."""
        activos = [s for s in self._sectores.values() if s.mode == SectorMode.ACTIVO]
        resultados = await asyncio.gather(
            *(self._start_tick_sector(s) for s in activos), return_exceptions=True
        )
        fallos = []
        for sector, r in zip(activos, resultados):
            clave = f"({sector.col},{sector.row})"
            if isinstance(r, Exception):
                fallos.append(f"{clave}: excepción {r!r}")
            elif not r.ok:
                fallos.append(f"{clave}: compute_tick lanzó excepción")
            elif r.timed_out:
                fallos.append(f"{clave}: timeout ({TICK_TIMEOUT_MS} ms)")
        if fallos:
            raise ErrorSincronizacion(
                f"Tick {self._tick_id}, StartTick: " + "; ".join(fallos)
            )

    async def _start_tick_sector(self, sector: SectorInfo):
        req = sector_pb.StartTickRequest(
            tick_id=self._tick_id,
            timeout_ms=TICK_TIMEOUT_MS,
        )
        return await sector.stub.StartTick(req)

    async def _resolver_movimientos(self, movimientos: list) -> list:
        """
        Resuelve los movimientos entre sectores, de uno en uno y en orden de
        id_elemento (determinista: si dos elementos quieren la misma casilla,
        gana el de menor id y el otro ve el slot ocupado).

        Para cada uno: RecibirElemento al sector destino (pregunta y crea en
        un solo RPC) y, solo si lo aceptó, ConfirmarSalida al origen, que lo
        elimina. Devuelve las celdas resultantes (destino y origen) para que
        Logica las reciba.

        - Rechazo normal (destino fuera del mapa, slot ocupado, sector no
          activo): el elemento SE QUEDA en su origen.
        - Fallo de RPC, o ConfirmarSalida fallido tras un "sí" del destino:
          ErrorSincronizacion (el elemento estaría duplicado o perdido).
        """
        celdas: list = []
        for origen, mov in sorted(movimientos, key=lambda om: om[1].id_elemento):
            destino = self._sector_para_posicion(mov.pos_destino.x, mov.pos_destino.y)
            if destino is None:
                logger.warning(
                    "Movimiento de %s rechazado: %s fuera del mapa.",
                    mov.id_elemento,
                    (mov.pos_destino.x, mov.pos_destino.y),
                )
                continue
            if destino.mode != SectorMode.ACTIVO:
                # Con la hibernación deshabilitada no debería ocurrir. Cargar
                # ahora su estado desde Logica lo dejaría desfasado (Logica
                # aún no tiene los cambios de este tick), así que se rechaza.
                logger.warning(
                    "Movimiento de %s rechazado: sector (%d,%d) no está ACTIVO.",
                    mov.id_elemento,
                    destino.col,
                    destino.row,
                )
                continue

            try:
                resp = await destino.stub.RecibirElemento(
                    sector_pb.RecibirElementoRequest(
                        tick_id=self._tick_id, movimiento=mov
                    )
                )
            except Exception as exc:
                raise ErrorSincronizacion(
                    f"RecibirElemento({mov.id_elemento}) falló: {exc!r}"
                ) from exc
            if not resp.ok:
                raise ErrorSincronizacion(
                    f"RecibirElemento({mov.id_elemento}) en "
                    f"({destino.col},{destino.row}): {resp.error}"
                )
            if not resp.aceptado:
                logger.info(
                    "Movimiento de %s rechazado por (%d,%d): %s",
                    mov.id_elemento,
                    destino.col,
                    destino.row,
                    resp.motivo_rechazo,
                )
                continue

            try:
                resp_o = await origen.stub.ConfirmarSalida(
                    sector_pb.ConfirmarSalidaRequest(
                        tick_id=self._tick_id,
                        id_elemento=mov.id_elemento,
                        pos_origen=mov.pos_origen,
                    )
                )
            except Exception as exc:
                raise ErrorSincronizacion(
                    f"ConfirmarSalida({mov.id_elemento}) falló: {exc!r}"
                ) from exc
            if not resp_o.ok:
                raise ErrorSincronizacion(
                    f"ConfirmarSalida({mov.id_elemento}) en "
                    f"({origen.col},{origen.row}): {resp_o.error}"
                )

            celdas.append(resp.celda_destino)
            celdas.append(resp_o.celda_origen)
        return celdas

    async def _fase_2(self) -> None:
        """
        Fase 2 (consolidación): recoge el delta de cada sector, resuelve los
        movimientos entre sectores, sincroniza Logica_Mundo y avanza el tiempo
        del mundo.

        CUALQUIER fallo de comunicación con un sector, o al aplicar el delta en
        Logica, es fatal (ErrorSincronizacion): los Sectores ya aplicaron los
        cambios del tick en su copia y Logica (el gold) no los tendría.
        """
        activos = [s for s in self._sectores.values() if s.mode == SectorMode.ACTIVO]
        resultados = await asyncio.gather(
            *(self._get_delta_sector(s) for s in activos), return_exceptions=True
        )

        fallos = []
        for sector, r in zip(activos, resultados):
            clave = f"({sector.col},{sector.row})"
            if isinstance(r, Exception):
                fallos.append(f"{clave}: excepción {r!r}")
            elif not r.ok:
                fallos.append(f"{clave}: {r.error}")
        if fallos:
            raise ErrorSincronizacion(
                f"Tick {self._tick_id}, GetDelta: " + "; ".join(fallos)
            )

        # Los sonidos de este tick se entregan en la fase 0 del siguiente.
        self._pending_sounds = {}
        celdas_cambiadas: list = []
        celdas_atmosfera_cambiadas: list = []
        movimientos: list = []  # (SectorInfo origen, MovimientoSaliente)
        bots_muertos: list[int] = []

        async with self._consolidacion_lock:
            for sector, delta in zip(activos, resultados):
                celdas_cambiadas.extend(delta.changed_cells)
                celdas_atmosfera_cambiadas.extend(delta.changed_atmosphere_cells)
                bots_muertos.extend(delta.dead_bot_ids)
                movimientos.extend((sector, m) for m in delta.movimientos_salientes)
                for sound in delta.emitted_sounds:
                    self._distribuir_sonido(sound)
                if self._delta_tiene_actividad(delta):
                    sector.ticks_sin_actividad = 0

            # Movimientos entre sectores. Sus celdas van DESPUÉS de las del
            # tick: Logica aplica las celdas en orden y gana la última, así
            # que la celda final de cada posición es la que ya refleja el
            # movimiento.
            celdas_cambiadas.extend(await self._resolver_movimientos(movimientos))

            if celdas_cambiadas:
                try:
                    await self._logica_client.actualizar_celdas(celdas_cambiadas)
                except Exception as exc:
                    raise ErrorSincronizacion(
                        f"actualizar_celdas falló en el tick {self._tick_id}: {exc!r}"
                    ) from exc

            if celdas_atmosfera_cambiadas:
                # NO fatal: cada tick reenvía el estado completo. Pero tampoco
                # debe abortar el resto de la fase.
                try:
                    await self._logica_client.actualizar_celdas_atmosfera(
                        celdas_atmosfera_cambiadas
                    )
                except Exception:
                    logger.exception(
                        "Tick %d: no se pudo actualizar la atmósfera.", self._tick_id
                    )

            for bot_id in bots_muertos:
                await self._logica_client.matar_bot(
                    bot_id, "avatar eliminado en sector", self._tick_id
                )

            await self._actualizar_modos_sector()
            await self._logica_client.avanzar_tick(self._tick_id)

        await self._reset_budgets()

    async def _get_delta_sector(self, sector: SectorInfo):
        req = sector_pb.GetDeltaRequest(tick_id=self._tick_id)
        return await sector.stub.GetDelta(req)

    def activar_modo_paso(self, activar: bool) -> tuple[bool, str]:
        """
        Activa/desactiva el modo tick a tick.

        No toca freeze()/resume(): si el sistema está congelado,
        activar esto no hace avanzar nada — _pause_event sigue
        bloqueando el bucle antes de llegar siquiera a mirar _modo_paso.
        """
        self._modo_paso = activar
        if activar:
            self._step_event.clear()
        else:
            self._step_event.set()
        logger.info("Modo tick a tick %s.", "activado" if activar else "desactivado")
        return True, ""

    def avanza_tick(self) -> tuple[bool, str]:
        """
        Autoriza avanzar EXACTAMENTE un tick, solo si el modo paso ya
        está activo. Deliberadamente NO activa el modo paso por su
        cuenta si está desactivado — así la consola no puede "entrar"
        en modo paso sin que quien llama lo haya pedido explícitamente
        con activar_modo_paso(True).
        """
        if not self._modo_paso:
            return False, "No se puede avanzar: modo_paso está desactivado."
        self._step_event.set()
        return True, ""

    async def close(self) -> None:
        """Cancela tareas de fondo y cierra los canales gRPC."""
        for t in list(self._tareas_fondo):
            t.cancel()
        if self._tareas_fondo:
            await asyncio.gather(*self._tareas_fondo, return_exceptions=True)
        canales = [i.channel for i in self._sectores.values() if i.channel is not None]
        if self._bots_channel is not None:
            canales.append(self._bots_channel)
        await asyncio.gather(*(c.close() for c in canales), return_exceptions=True)

    def _distribuir_sonido(self, sound: common_pb.SoundEvent) -> None:
        lx = sound.origin.x // SOUND_MAP_CELL_SIZE
        ly = sound.origin.y // SOUND_MAP_CELL_SIZE

        radio_lr = math.ceil(MAX_SOUND_DISTANCE / SOUND_MAP_CELL_SIZE)

        for col in range(self.COLS):
            for row in range(self.ROWS):
                sx = (col * SECTOR_SIZE) // SOUND_MAP_CELL_SIZE
                sy = (row * SECTOR_SIZE) // SOUND_MAP_CELL_SIZE
                if abs(sx - lx) <= radio_lr and abs(sy - ly) <= radio_lr:
                    key = (col, row)
                    self._pending_sounds.setdefault(key, []).append(sound)

    async def _actualizar_modos_sector(self) -> None:
        """
        DESHABILITADO a propósito: todos los sectores tienen suelo y atmósfera
        que procesar, así que ninguno se duerme por inactividad. SectorMode,
        set_mode, _vecinos, ticks_sin_actividad y _modos_previos_freeze se
        conservan para reactivarlo; la lógica original está en el historial de git.
        """

        """
        Codigo encargado de dormir a los sectores.
        Al todos tener suelo y atmosfera que procesar, ha
        sido aparcado.
        Potencialmente se le puede dar otro uso en el futuro.
        """
        # for info in self._sectores.values():
        #     if info.mode == SectorMode.ACTIVO:
        #         info.ticks_sin_actividad += 1
        #         if info.ticks_sin_actividad >= TICKS_ANTES_DE_DORMIR:
        #             await self._set_sector_mode(info, SectorMode.DORMIDO)
        #         else:
        #             for vecino in self._vecinos(info):
        #                 if vecino.mode == SectorMode.INACTIVO:
        #                     await self._set_sector_mode(vecino, SectorMode.DORMIDO)

    async def _set_sector_mode(self, info: SectorInfo, mode: SectorMode) -> None:
        if info.mode == mode:
            return
        req = sector_pb.SetSectorModeRequest(mode=mode.value)
        try:
            resp = await info.stub.SetSectorMode(req)
            if resp.ok:
                info.mode = mode
                logger.debug("Sector (%d,%d) → %s", info.col, info.row, mode.name)
            else:
                logger.warning(
                    "SetSectorMode falló en (%d,%d): %s", info.col, info.row, resp.error
                )
        except grpc.aio.AioRpcError as e:
            logger.error("gRPC error SetSectorMode (%d,%d): %s", info.col, info.row, e)

    def activar_sector_en_posicion(self, x: int, y: int) -> None:
        info = self._sector_para_posicion(x, y)
        if info and info.mode != SectorMode.ACTIVO:
            self._lanzar_en_segundo_plano(self._activar_sector(info))

    def _lanzar_en_segundo_plano(self, coro) -> None:
        tarea = asyncio.create_task(coro)
        self._tareas_fondo.add(tarea)

        def _al_terminar(t: asyncio.Task) -> None:
            self._tareas_fondo.discard(t)
            if t.cancelled():
                return
            exc = t.exception()
            if isinstance(exc, ErrorFatal):
                self._escalar_fatal(exc)
            elif exc is not None:
                logger.error("Tarea en segundo plano falló: %r", exc)

        tarea.add_done_callback(_al_terminar)

    def sectores_caidos(self) -> list[str]:
        """
        Devuelve los identificadores "col_row" de sectores con
        fallos_consecutivos >= FALLOS_CONSECUTIVOS_SECTOR_CAIDO —
        probable spot terminado. No hace ping adicional: reusa los
        fallos que ya se observan en _fase_1/_fase_2 durante el tick
        normal.
        """
        return [
            f"{info.col}_{info.row}"
            for info in self._sectores.values()
            if info.fallos_consecutivos >= FALLOS_CONSECUTIVOS_SECTOR_CAIDO
        ]

    async def freeze(self) -> None:
        if self._state != SystemState.RUNNING:
            return

        logger.info("FREEZE iniciado (tick %d)", self._tick_id)
        self._state = SystemState.PAUSING
        self._pause_event.clear()

        async with self._tick_lock:  # espera a que acabe el tick en curso
            pass

        try:
            await self._bots_stub.FreezeAll(bots_pb.FreezeAllRequest())
        except grpc.aio.AioRpcError as e:
            logger.error("Error al congelar Gestor_Bots: %s", e)

        self._modos_previos_freeze = {
            (info.col, info.row): info.mode
            for info in self._sectores.values()
            if info.mode in (SectorMode.ACTIVO, SectorMode.DORMIDO)
        }
        tareas = [
            self._set_sector_mode(self._sectores[clave], SectorMode.INACTIVO)
            for clave in self._modos_previos_freeze
        ]
        if tareas:
            await asyncio.gather(*tareas, return_exceptions=True)

        self._state = SystemState.PAUSED
        logger.info("Sistema completamente congelado.")

    async def resume(self) -> None:
        if self._state != SystemState.PAUSED:
            return

        logger.info("RESUME (tick %d)", self._tick_id)
        self._state = SystemState.RESUMING

        try:
            await self._distribute_gold_to_sectors()
        except Exception as exc:
            self._state = SystemState.PAUSED
            if isinstance(exc, ErrorFatal):
                self._escalar_fatal(exc)
            raise

        for clave, modo in self._modos_previos_freeze.items():
            await self._set_sector_mode(self._sectores[clave], modo)
        self._modos_previos_freeze = {}

        try:
            await self._bots_stub.ResumeAll(bots_pb.ResumeAllRequest())
        except grpc.aio.AioRpcError as e:
            logger.error("Error al reanudar Gestor_Bots: %s", e)

        self._state = SystemState.RUNNING
        self._pause_event.set()
        logger.info("Sistema reanudado.")

    @staticmethod
    def _calcular_intervalo(ticks_per_second: int) -> float:
        return (1.0 / ticks_per_second) if ticks_per_second > 0 else 0.0

    async def set_tick_rate(self, ticks_per_second: int) -> None:

        self._tick_rate = ticks_per_second
        self._tick_interval = self._calcular_intervalo(ticks_per_second)
        logger.info(
            "Cadencia de ticks cambiada a %s",
            "sin límite" if ticks_per_second <= 0 else f"{ticks_per_second}/s",
        )

    async def _save_snapshot(self) -> None:

        snapshot_id = f"{self._tick_id:010d}"
        path = SNAPSHOT_DIR / f"mundo_{snapshot_id}.json"

        async with self._consolidacion_lock:
            data = {
                "tick_id": int(self._tick_id),
                "snapshot_id": snapshot_id,
                "fecha": datetime.datetime.now().isoformat(),
                "sectores": [
                    {
                        "col": info.col,
                        "row": info.row,
                        "address": info.address,
                        "mode": info.mode.value,
                    }
                    for info in self._sectores.values()
                ],
            }

        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

        await self._logica_client.save_snapshot(snapshot_id)

        self._snapshot_id = snapshot_id
        logger.info("Snapshot guardado: %s", path)

        self._purgar_snapshots_antiguos()

    def _purgar_snapshots_antiguos(self) -> None:
        snapshots = sorted(
            SNAPSHOT_DIR.glob("mundo_*.json"),
            key=lambda p: p.stem.removeprefix("mundo_"),
        )
        sobrantes = max(0, len(snapshots) - SNAPSHOT_MAX)
        for path in snapshots[:sobrantes]:
            path.unlink(missing_ok=True)
            logger.debug("Snapshot antiguo purgado: %s", path)

    async def _deep_save(self) -> None:
        logger.info("Guardado profundo iniciado (tick %d)", self._tick_id)

        estaba_corriendo = self._state == SystemState.RUNNING

        await self.freeze()
        try:
            snapshot_id = f"{self._tick_id:010d}_deep"
            self._snapshot_id = snapshot_id

            path = SNAPSHOT_DIR / f"mundo_{snapshot_id}.json"
            async with self._consolidacion_lock:
                data = {
                    "tick_id": self._tick_id,
                    "snapshot_id": snapshot_id,
                    "fecha": datetime.datetime.now().isoformat(),
                    "sectores": [
                        {
                            "col": info.col,
                            "row": info.row,
                            "address": info.address,
                            "mode": info.mode.value,
                        }
                        for info in self._sectores.values()
                    ],
                }
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            await self._logica_client.save_snapshot(snapshot_id)

            try:
                await self._bots_stub.SaveSnapshot(
                    bots_pb.SaveSnapshotRequest(snapshot_id=snapshot_id)
                )
            except grpc.aio.AioRpcError as e:
                logger.error("Error al pedir snapshot a Gestor_Bots: %s", e)

            tareas_sectores = []
            for info in self._sectores.values():
                if info.stub is not None:
                    tareas_sectores.append(
                        info.stub.SaveSnapshot(
                            sector_pb.SaveSnapshotRequest(snapshot_id=snapshot_id)
                        )
                    )
            resultados = await asyncio.gather(*tareas_sectores, return_exceptions=True)
            for info, res in zip(self._sectores.values(), resultados):
                if isinstance(res, Exception):
                    logger.error(
                        "SaveSnapshot falló en sector (%d,%d): %s",
                        info.col,
                        info.row,
                        res,
                    )
                elif not res.ok:
                    logger.warning(
                        "SaveSnapshot error en sector (%d,%d): %s",
                        info.col,
                        info.row,
                        res.error,
                    )

            logger.info("Guardado profundo completado. snapshot_id=%s", snapshot_id)
        finally:
            if estaba_corriendo:
                await self.resume()

    def _latest_snapshot_path(self) -> Optional[Path]:
        snapshots = sorted(SNAPSHOT_DIR.glob("mundo_*.json"))
        return snapshots[-1] if snapshots else None

    async def _distribute_gold_to_sectors(self) -> None:
        """Carga el estado gold en todos los sectores en paralelo. Espera a
        TODOS y relanza el primer fallo (antes se ignoraban los resultados)."""
        infos = [i for i in self._sectores.values() if i.stub is not None]
        resultados = await asyncio.gather(
            *(self._load_sector_state(i) for i in infos), return_exceptions=True
        )
        for r in resultados:
            if isinstance(r, Exception):
                raise r

    async def _load_sector_state(self, info: SectorInfo) -> None:
        x0, y0 = info.col * SECTOR_SIZE, info.row * SECTOR_SIZE
        x1, y1 = x0 + SECTOR_SIZE, y0 + SECTOR_SIZE
        # Rectángulo en espacio de atmósfera: exacto porque
        # Sector._validar_escala_atmosfera exige que ATMOSFERA_ESCALA divida SECTOR_SIZE.
        ax0, ay0 = x0 // ATMOSFERA_ESCALA, y0 // ATMOSFERA_ESCALA
        ax1, ay1 = x1 // ATMOSFERA_ESCALA, y1 // ATMOSFERA_ESCALA
        try:
            cells = await self._logica_client.obtener_celdas_en_region(
                min_pos=(x0, y0), max_pos=(x1, y1)
            )
            atmosphere_cells = (
                await self._logica_client.obtener_celdas_atmosfera_en_region(
                    min_pos=(ax0, ay0), max_pos=(ax1, ay1)
                )
            )
            bots = await self._logica_client.obtener_bots_en_region(
                min_pos=(x0, y0), max_pos=(x1, y1)
            )
            resp = await info.stub.LoadState(
                sector_pb.LoadStateRequest(
                    cells=cells, atmosphere_cells=atmosphere_cells, bots=bots
                )
            )
        except Exception as exc:
            raise ErrorCargaSector(
                f"LoadState de ({info.col},{info.row}) falló: {exc!r}"
            ) from exc
        if not resp.ok:
            raise ErrorCargaSector(
                f"LoadState rechazado en ({info.col},{info.row}): {resp.error}"
            )

    async def _reset_budgets(self) -> None:
        try:
            await self._bots_stub.ResetBudgets(bots_pb.ResetBudgetsRequest())
        except grpc.aio.AioRpcError as e:
            logger.error("Error al resetear presupuestos: %s", e)

    async def _calcular_ghost_zone(self, info: SectorInfo) -> list:
        x0 = info.col * SECTOR_SIZE
        y0 = info.row * SECTOR_SIZE
        x1 = x0 + SECTOR_SIZE
        y1 = y0 + SECTOR_SIZE
        gx0 = x0 - MAX_VISION_DISTANCE
        gy0 = y0 - MAX_VISION_DISTANCE
        gx1 = x1 + MAX_VISION_DISTANCE
        gy1 = y1 + MAX_VISION_DISTANCE

        return await self._logica_client.obtener_celdas_en_region(
            min_pos=(gx0, gy0),
            max_pos=(gx1, gy1),
            excluir_min=(x0, y0),
            excluir_max=(x1, y1),
        )

    async def _calcular_ghost_zone_atmosfera(self, info: SectorInfo) -> list:
        """
        Análogo a _calcular_ghost_zone, pero en espacio de atmósfera y
        con margen 1 (adyacencia-8) en vez de MAX_VISION_DISTANCE -- la
        difusión atmosférica solo mira al vecino inmediato. El
        rectángulo propio del sector en espacio de atmósfera es exacto
        (sin bloques a caballo) gracias a
        Sector._validar_escala_atmosfera.
        """
        ax0 = (info.col * SECTOR_SIZE) // ATMOSFERA_ESCALA
        ay0 = (info.row * SECTOR_SIZE) // ATMOSFERA_ESCALA
        ax1 = ((info.col + 1) * SECTOR_SIZE) // ATMOSFERA_ESCALA
        ay1 = ((info.row + 1) * SECTOR_SIZE) // ATMOSFERA_ESCALA

        return await self._logica_client.obtener_celdas_atmosfera_en_region(
            min_pos=(ax0 - 1, ay0 - 1),
            max_pos=(ax1 + 1, ay1 + 1),
            excluir_min=(ax0, ay0),
            excluir_max=(ax1, ay1),
        )

    def _sector_para_posicion(self, x: int, y: int) -> Optional[SectorInfo]:
        col = x // SECTOR_SIZE
        row = y // SECTOR_SIZE
        return self._sectores.get((col, row))

    def _vecinos(self, info: SectorInfo) -> list[SectorInfo]:
        resultado = []
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                vecino = self._sectores.get((info.col + dc, info.row + dr))
                if vecino:
                    resultado.append(vecino)
        return resultado

    async def _connect_sector(self, info: SectorInfo) -> None:
        info.channel = grpc.aio.insecure_channel(info.address)
        info.stub = sector_grpc.SectorServiceStub(info.channel)

    def _sector_address(self, col: int, row: int) -> str:
        env_key = f"SECTOR_ADDR_C{col}_R{row}"
        addr = os.getenv(env_key)
        if addr:
            return addr
        port = SECTOR_BASE_PORT + col * self.ROWS + row
        return f"{SECTOR_HOST}:{port}"
