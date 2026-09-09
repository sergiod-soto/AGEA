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
from numpy import uint64

from Config.settings import DEEP_SAVE_INTERVAL_TICKS, DEFAULT_TICK_RATE, GESTOR_BOTS_ADDRESS, GRID_HEIGHT, GRID_WIDTH, MAX_VISION_DISTANCE, SECTOR_SIZE, SNAPSHOT_DIR, SNAPSHOT_INTERVAL_TICKS, SOUND_MAP_CELL_SIZE, TICK_TIMEOUT_MS, TICKS_ANTES_DE_DORMIR
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


FALLOS_CONSECUTIVOS_SECTOR_CAIDO = int(os.getenv("FALLOS_CONSECUTIVOS_SECTOR_CAIDO", 3))
SNAPSHOT_MAX = int(os.getenv("SNAPSHOT_MAX", "20"))


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

        self._tick_id: uint64 = uint64(0)
        self._snapshot_id: str = ""

        self._state: SystemState = SystemState.RUNNING
        self._modo_paso: bool = False
        self._step_event: asyncio.Event = asyncio.Event()
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()
        self._tick_rate: int = DEFAULT_TICK_RATE
        self._tick_interval: float = self._calcular_intervalo(DEFAULT_TICK_RATE)

        self._bots_channel: Optional[grpc.aio.Channel] = None
        self._bots_stub = None

        self._consolidacion_lock: asyncio.Lock = asyncio.Lock()

        self._pending_sounds = {}

    def _delta_tiene_actividad(self, delta) -> bool:
        return bool(delta.changed_cells or delta.outgoing_bots or delta.emitted_sounds)

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
        logger.info("Inicio limpio. Creando %d×%d sectores.", self.COLS, self.ROWS)
        for col in range(self.COLS):
            for row in range(self.ROWS):
                address = self._sector_address(col, row)
                info = SectorInfo(col=col, row=row, address=address)
                self._sectores[(col, row)] = info
                await self._connect_sector(info)
                await self._set_sector_mode(info, SectorMode.INACTIVO)

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

        for s in data["sectores"]:
            col, row = s["col"], s["row"]
            info = SectorInfo(
                col=col,
                row=row,
                address=s["address"],
                mode=SectorMode(s["mode"]),
            )
            self._sectores[(col, row)] = info
            await self._connect_sector(info)

        await self._logica_client.load_state(self._snapshot_id)
        await self._distribute_gold_to_sectors()

    async def run_loop(self) -> None:
        while True:
            await self._pause_event.wait()

            if self._modo_paso:
                await self._step_event.wait()
                self._step_event.clear()

            t0 = time.monotonic()
            await self._run_tick()
            elapsed = time.monotonic() - t0

            self._tick_id += 1

            if self._tick_id % SNAPSHOT_INTERVAL_TICKS == 0:
                asyncio.create_task(self._save_snapshot())

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

        self._pending_sounds: dict[tuple[int, int], list] = {}

        tareas = []
        for sector in activos_y_dormidos:
            tareas.append(self._enviar_ghost_zone(sector))
            tareas.append(self._enviar_sonidos(sector))

        await asyncio.gather(*tareas, return_exceptions=True)

    async def _enviar_ghost_zone(self, sector: SectorInfo) -> None:
        ghost_cells = await self._calcular_ghost_zone(sector)
        if not ghost_cells:
            return
        req = sector_pb.SetGhostZoneRequest(  # type: ignore
            tick_id=self._tick_id,
            ghost_cells=ghost_cells,
        )
        try:
            resp = await sector.stub.SetGhostZone(req)  # type: ignore
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

        async with self._consolidacion_lock:
            for sector, resultado in zip(activos, resultados):
                if isinstance(resultado, Exception):
                    logger.error(
                        "Error en GetDelta sector (%d,%d): %s",
                        sector.col,
                        sector.row,
                        resultado,
                    )
                    # NUEVO: cuenta también como fallo de comunicación.
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

                for bot in resultado.outgoing_bots:
                    bots_migrando.append((sector, bot))

                for sound in resultado.emitted_sounds:
                    self._distribuir_sonido(sound)

                if self._delta_tiene_actividad(resultado):
                    sector.ticks_sin_actividad = 0

            if celdas_cambiadas:
                await self._logica_client.actualizar_celdas(celdas_cambiadas)

            await self._resolver_migraciones(bots_migrando)

            await self._actualizar_modos_sector()

            cambios_globales = await self._logica_client.avanzar_elementos_globales(
                self._tick_id
            )
            # TODO: distribuir cambios_globales a sectores que lo necesiten

        await self._reset_budgets()

    async def _get_delta_sector(self, sector: SectorInfo):
        req = sector_pb.GetDeltaRequest(tick_id=self._tick_id)
        return await sector.stub.GetDelta(req)

    async def _resolver_migraciones(
        self,
        bots_migrando: list[tuple[SectorInfo, sector_pb.MigratingBot]],
    ) -> None:
        for origen, mbot in bots_migrando:
            destino = self._sector_para_posicion(mbot.target_pos.x, mbot.target_pos.y)
            if destino is None:
                logger.warning(
                    "Bot %s migró fuera del mapa (%d,%d) — eliminado",
                    mbot.bot.bot_id,
                    mbot.target_pos.x,
                    mbot.target_pos.y,
                )
                continue
            if destino.mode == SectorMode.INACTIVO:
                await self._set_sector_mode(destino, SectorMode.ACTIVO)

            req = sector_pb.AddMigratingBotRequest(
                tick_id=self._tick_id,
                bot=mbot.bot,
            )
            try:
                resp = await destino.stub.AddMigratingBot(req)
                if not resp.ok:
                    logger.warning(
                        "AddMigratingBot falló para bot %s en (%d,%d): %s",
                        mbot.bot.bot_id,
                        destino.col,
                        destino.row,
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

        from Core.Entities.Mundo.mapa_config import (
            MAX_SOUND_DISTANCE,
        )

        radio_lr = math.ceil(MAX_SOUND_DISTANCE / SOUND_MAP_CELL_SIZE)

        for col in range(self.COLS):
            for row in range(self.ROWS):
                sx = (col * SECTOR_SIZE) // SOUND_MAP_CELL_SIZE
                sy = (row * SECTOR_SIZE) // SOUND_MAP_CELL_SIZE
                if abs(sx - lx) <= radio_lr and abs(sy - ly) <= radio_lr:
                    key = (col, row)
                    self._pending_sounds.setdefault(key, []).append(sound)

    async def _actualizar_modos_sector(self) -> None:
        for info in self._sectores.values():
            if info.mode == SectorMode.ACTIVO:
                info.ticks_sin_actividad += 1
                if info.ticks_sin_actividad >= TICKS_ANTES_DE_DORMIR:
                    await self._set_sector_mode(info, SectorMode.DORMIDO)
                else:
                    for vecino in self._vecinos(info):
                        if vecino.mode == SectorMode.INACTIVO:
                            await self._set_sector_mode(vecino, SectorMode.DORMIDO)

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
        if info and info.mode == SectorMode.INACTIVO:
            asyncio.create_task(self._set_sector_mode(info, SectorMode.ACTIVO))

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

        tareas = []
        for info in self._sectores.values():
            if info.mode in (SectorMode.ACTIVO, SectorMode.DORMIDO):
                tareas.append(
                    info.stub.SetSectorMode(
                        sector_pb.SetSectorModeRequest(
                            mode=sector_pb.SectorMode.Value("INACTIVO")
                        )
                    )
                )
        if tareas:
            await asyncio.gather(*tareas, return_exceptions=True)

        self._state = SystemState.PAUSED
        logger.info("Sistema completamente congelado.")

    async def resume(self) -> None:
        if self._state != SystemState.PAUSED:
            return

        logger.info("RESUME (tick %d)", self._tick_id)
        self._state = SystemState.RESUMING

        await self._distribute_gold_to_sectors()

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

    def _purgar_snapshots_antiguos(self) -> None:
        snapshots = sorted(
            SNAPSHOT_DIR.glob("mundo_*.json"),
            key=lambda p: p.stem.removeprefix("mundo_"),
        )
        sobrantes = len(snapshots) - SNAPSHOT_MAX
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
                    "tick_id": int(self._tick_id),  # FIX: uint64 -> int
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
        req = sector_pb.LoadStateRequest(cells=cells)
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
        base_port = int(os.getenv("SECTOR_BASE_PORT", 50100))
        host = os.getenv("SECTOR_HOST", "localhost")
        port = base_port + col * self.ROWS + row
        return f"{host}:{port}"
