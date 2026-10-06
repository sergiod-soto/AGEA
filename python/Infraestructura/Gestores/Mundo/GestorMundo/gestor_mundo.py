# Infraestructura/Gestores/Mundo/Gestor_Mundo/gestor_mundo.py


import asyncio
import datetime
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
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2_grpc as sector_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2_grpc as bots_grpc,
)
from Infraestructura.Gestores.Mundo.Sector.sector import SectorMode
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2 as bots_pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as sector_pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

logger = logging.getLogger(__name__)


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

        self._bots_channel: Optional[grpc.aio.Channel] = None
        self._bots_stub = None

        self._consolidacion_lock: asyncio.Lock = asyncio.Lock()

        self._pending_sounds = {}

        self._modos_previos_freeze: dict[tuple[int, int], SectorMode] = {}

        self._tareas_fondo: set[asyncio.Task] = set()

    def _delta_tiene_actividad(self, delta) -> bool:
        return bool(
            delta.changed_cells
            or delta.outgoing_bots
            or delta.emitted_sounds
            or delta.movimientos_externos
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
        # logger.info("Inicio limpio. Creando %d×%d sectores.", self.COLS, self.ROWS)
        # for col in range(self.COLS):
        #     for row in range(self.ROWS):
        #         address = self._sector_address(col, row)
        #         info = SectorInfo(col=col, row=row, address=address)
        #         self._sectores[(col, row)] = info
        #         await self._connect_sector(info)
        #         await self._set_sector_mode(info, SectorMode.INACTIVO)
        logger.info("Inicio limpio. Creando %d×%d sectores.", self.COLS, self.ROWS)
        for col in range(self.COLS):
            for row in range(self.ROWS):
                address = self._sector_address(col, row)
                info = SectorInfo(col=col, row=row, address=address)
                self._sectores[(col, row)] = info
                await self._connect_sector(info)
                await self._load_sector_state(info)
                await self._set_sector_mode(info, SectorMode.ACTIVO)

    async def _restore_from_snapshot(self) -> None:
        snapshot_path = self._latest_snapshot_path()
        if snapshot_path is None:
            logger.warning("No se encontró snapshot. Iniciando limpio.")
            await self._init_fresh()
            return

        logger.info("Restaurando desde %s", snapshot_path)
        import json

        data = json.loads(snapshot_path.read_text())

        self._tick_id = data["tick_id"]
        self._snapshot_id = data["snapshot_id"]

        self._tick_id = data["tick_id"]
        self._snapshot_id = data["snapshot_id"]

        for s in data["sectores"]:
            col, row = s["col"], s["row"]
            info = SectorInfo(col=col, row=row, address=s["address"])
            self._sectores[(col, row)] = info
            await self._connect_sector(info)

        await self._logica_client.load_state(self._snapshot_id)
        # Carga el estado en cada sector ANTES de activarlo (mismo orden
        # que _init_fresh).
        await self._distribute_gold_to_sectors()

        for info in self._sectores.values():
            await self._set_sector_mode(info, SectorMode.ACTIVO)

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
                await self._run_tick()
            except Exception:
                logger.exception("Tick %d abortado por excepción.", self._tick_id)
            elapsed = time.monotonic() - t0

            self._tick_id += 1

            if self._tick_id % SNAPSHOT_INTERVAL_TICKS == 0:
                # FIX B3: con referencia guardada y fallo registrado.
                self._lanzar_en_segundo_plano(self._save_snapshot())

            if self._tick_id % DEEP_SAVE_INTERVAL_TICKS == 0:
                await self._deep_save()

            logger.debug("Tick %d completado en %.3fs", self._tick_id, elapsed)
            if self._tick_interval > 0:
                sobrante = self._tick_interval - elapsed
                if sobrante > 0:
                    await asyncio.sleep(sobrante)

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
        """
        Ordena a todos los sectores ACTIVOS que computen en paralelo.

        cada excepción/timeout incrementa sector.fallos_consecutivos;
        cada éxito lo resetea a 0.
        """
        activos = [s for s in self._sectores.values() if s.mode == SectorMode.ACTIVO]
        tareas = [self._start_tick_sector(s) for s in activos]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)

        for sector, resultado in zip(activos, resultados):
            if isinstance(resultado, Exception):
                logger.error(
                    "Error en StartTick sector (%d,%d): %s",
                    sector.col,
                    sector.row,
                    resultado,
                )
                sector.fallos_consecutivos += 1
            elif resultado.timed_out:
                logger.warning(
                    "Sector (%d,%d) no terminó a tiempo (tick %d)",
                    sector.col,
                    sector.row,
                    self._tick_id,
                )
                sector.fallos_consecutivos += 1
            else:
                sector.fallos_consecutivos = 0

    async def _start_tick_sector(self, sector: SectorInfo):
        req = sector_pb.StartTickRequest(
            tick_id=self._tick_id,
            timeout_ms=TICK_TIMEOUT_MS,
        )
        return await sector.stub.StartTick(req)

    async def _fase_2(self) -> None:
        activos = [s for s in self._sectores.values() if s.mode == SectorMode.ACTIVO]

        tareas = [self._get_delta_sector(s) for s in activos]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)

        self._pending_sounds: dict[tuple[int, int], list] = {}
        bots_migrando: list[tuple[SectorInfo, sector_pb.MigratingBot]] = []
        celdas_cambiadas: list = []
        celdas_atmosfera_cambiadas: list = []
        movimientos_externos: list = []
        bots_muertos: list[int] = []

        async with self._consolidacion_lock:
            for sector, resultado in zip(activos, resultados):
                if isinstance(resultado, Exception):
                    logger.error(
                        "Error en GetDelta sector (%d,%d): %s",
                        sector.col,
                        sector.row,
                        resultado,
                    )
                    # Cuenta también como fallo de comunicación.
                    sector.fallos_consecutivos += 1
                    continue
                if not resultado.ok:
                    logger.warning(
                        "GetDelta falló en (%d,%d): %s",
                        sector.col,
                        sector.row,
                        resultado.error,
                    )
                    continue

                celdas_cambiadas.extend(resultado.changed_cells)
                celdas_atmosfera_cambiadas.extend(resultado.changed_atmosphere_cells)
                movimientos_externos.extend(resultado.movimientos_externos)
                bots_muertos.extend(resultado.dead_bot_ids)
                bots_migrando.extend((sector, b) for b in resultado.outgoing_bots)

                for sound in resultado.emitted_sounds:
                    self._distribuir_sonido(sound)

                if self._delta_tiene_actividad(resultado):
                    sector.ticks_sin_actividad = 0

            rechazados: dict[int, Optional[tuple[int, int]]] = {}
            if celdas_cambiadas or movimientos_externos:
                rechazados = await self._logica_client.actualizar_celdas(
                    celdas_cambiadas, movimientos_externos
                )

            if celdas_atmosfera_cambiadas:
                await self._logica_client.actualizar_celdas_atmosfera(
                    celdas_atmosfera_cambiadas
                )

            for bot_id in bots_muertos:
                await self._logica_client.matar_bot(
                    bot_id, "avatar eliminado en sector", int(self._tick_id)
                )

            await self._resolver_migraciones(
                bots_migrando, movimientos_externos, rechazados
            )

            await self._actualizar_modos_sector()

            # cambios_globales = await self._logica_client.avanzar_elementos_globales(
            #     self._tick_id
            # )
            await self._logica_client.avanzar_tick(self._tick_id)
            # TODO: distribuir cambios_globales a sectores que lo necesiten

        await self._reset_budgets()

    async def recargar_mundo_tras_generacion(self) -> None:
        """
        Fuerza a todos los Sectores a recargar su terreno y atmósfera
        desde el estado gold de LogicaMundo. Pensado para llamarse UNA
        VEZ, justo después de que el generador de mundo termine de crear
        todos los elementos (vía LogicaMundoClient.crear_elemento()).

        Por qué hace falta: los Sectores arrancan ANTES de que exista el
        mundo generado (con su malla vacía o la de un snapshot previo).
        Cada crear_elemento() del generador sí actualiza el estado gold
        de LogicaMundo (incluidas las cachés de Celda_Atmosfera, vía sus
        propios hooks), pero NO empuja ese cambio a la copia local de
        cada Sector -- eso solo ocurre cuando el Sector recibe un
        LoadState. Reutiliza _distribute_gold_to_sectors, el mismo
        mecanismo que ya usa _restore_from_snapshot.
        """
        logger.info("Recargando estado de todos los sectores tras generación de mundo.")
        await self._distribute_gold_to_sectors()

    async def _get_delta_sector(self, sector: SectorInfo):
        req = sector_pb.GetDeltaRequest(tick_id=self._tick_id)
        return await sector.stub.GetDelta(req)

    async def _resolver_migraciones(
        self,
        bots_migrando: list[tuple[SectorInfo, sector_pb.MigratingBot]],
        movimientos_externos: list,
        rechazados: dict[int, Optional[tuple[int, int]]],
    ) -> None:
        """Entrega cada bot migrante a su Sector destino, junto con su avatar
        serializado. Si Logica rechazó el movimiento, el bot NO migra: se devuelve
        a su Sector origen.
        """

        movs = {int(m.id_elemento): m for m in movimientos_externos}

        for origen, mbot in bots_migrando:
            eid = int(mbot.bot.id_elemento)
            mov = movs.get(eid)
            avatar = mov.elemento if mov is not None else b""

            if eid in rechazados:
                pos_devuelta = rechazados[eid]
                if pos_devuelta is None:
                    # Caso residual: no cupo ni en destino ni en origen y
                    # Logica eliminó el avatar -> hay que terminar el script.
                    await self._logica_client.matar_bot(
                        mbot.bot.bot_id, "colisión sin sitio", self._tick_id
                    )
                    continue

                mbot.bot.pos.x, mbot.bot.pos.y = pos_devuelta
                await self._enviar_bot(origen, mbot.bot, avatar)
                continue

            destino = self._sector_para_posicion(mbot.target_pos.x, mbot.target_pos.y)
            if destino is None:
                # TODO: hoy el avatar SÍ queda colocado en Mundo
                # fuera del mapa, aunque este log diga otra cosa.
                logger.warning(
                    "Bot %s migró fuera del mapa (%d,%d).",
                    mbot.bot.bot_id,
                    mbot.target_pos.x,
                    mbot.target_pos.y,
                )
                continue

            await self._activar_sector(destino)
            await self._enviar_bot(destino, mbot.bot, avatar)

    async def _enviar_bot(self, sector: SectorInfo, bot, avatar: bytes) -> None:
        """Envía un bot (con su avatar serializado) a un Sector. Se
        factoriza porque lo usan dos caminos: la migración normal y la
        devolución al origen cuando Logica rechazó el movimiento."""
        req = sector_pb.AddMigratingBotRequest(
            tick_id=self._tick_id, bot=bot, elemento=avatar
        )
        try:
            resp = await sector.stub.AddMigratingBot(req)
            if not resp.ok:
                logger.warning(
                    "AddMigratingBot falló para bot %s en (%d,%d): %s",
                    bot.bot_id,
                    sector.col,
                    sector.row,
                    resp.error,
                )
        except grpc.aio.AioRpcError as e:
            logger.error("gRPC error AddMigratingBot: %s", e)

    def activar_modo_paso(self, activar: bool) -> tuple[bool, str]:
        """
        Activa/desactiva el modo tick a tick.

        No toca freeze()/resume(): si el sistema está congelado,
        activar esto no hace avanzar nada — _pause_event sigue
        bloqueando el bucle antes de llegar siquiera a mirar _modo_paso.
        """
        self._modo_paso = activar
        if not activar:
            # Libera cualquier espera pendiente: si no, el bucle se
            # quedaría colgado esperando un avanza_tick() que ya no va
            # a llegar al volver al modo automático.
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
        DESHABILITADO a propósito: mientras no se retome la hibernación,
        ningún sector se duerme por inactividad. SectorMode, set_mode y
        _modos_previos_freeze se conservan para reactivarlo. La lógica
        original (ticks_sin_actividad >= TICKS_ANTES_DE_DORMIR -> DORMIDO,
        vecinos INACTIVO -> DORMIDO) está en el historial de git.
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
            if not t.cancelled() and t.exception() is not None:
                logger.error("Tarea en segundo plano falló: %r", t.exception())

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
        except Exception:
            self._state = SystemState.PAUSED  # permite reintentar resume()
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
        import json

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

    # Infraestructura/Gestores/Mundo/Gestor_Mundo/gestor_mundo.py
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

            import json

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
        tareas = []
        for info in self._sectores.values():
            if info.stub is not None:
                tareas.append(self._load_sector_state(info))
        await asyncio.gather(*tareas, return_exceptions=True)

    async def _load_sector_state(self, info: SectorInfo) -> None:
        x0 = info.col * SECTOR_SIZE
        y0 = info.row * SECTOR_SIZE
        x1 = x0 + SECTOR_SIZE
        y1 = y0 + SECTOR_SIZE

        cells = await self._logica_client.obtener_celdas_en_region(
            min_pos=(x0, y0), max_pos=(x1, y1)
        )

        # Rectángulo del sector en espacio de atmósfera -- exacto (sin
        # bloques a caballo) gracias a que Sector._validar_escala_atmosfera
        # exige que ATMOSFERA_ESCALA divida SECTOR_SIZE.
        ax0 = x0 // ATMOSFERA_ESCALA
        ay0 = y0 // ATMOSFERA_ESCALA
        ax1 = x1 // ATMOSFERA_ESCALA
        ay1 = y1 // ATMOSFERA_ESCALA
        atmosphere_cells = await self._logica_client.obtener_celdas_atmosfera_en_region(
            min_pos=(ax0, ay0), max_pos=(ax1, ay1)
        )

        req = sector_pb.LoadStateRequest(cells=cells, atmosphere_cells=atmosphere_cells)
        try:
            resp = await info.stub.LoadState(req)
            if not resp.ok:
                logger.warning(
                    "LoadState falló en (%d,%d): %s", info.col, info.row, resp.error
                )
        except grpc.aio.AioRpcError as e:
            logger.error("gRPC error LoadState (%d,%d): %s", info.col, info.row, e)

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
