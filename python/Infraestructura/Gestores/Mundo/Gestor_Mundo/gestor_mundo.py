"""
gestor_mundo.py
---------------
Gestor central del mundo. Responsabilidades:

  - Mantener el estado gold (celdas + sectores + elementos globales)
  - Ejecutar el ciclo de tick en tres fases (FASE 0 / 1 / 2)
  - Gestionar el ciclo de vida de los sectores (crear, registrar, cambiar modo)
  - Emitir snapshots periódicos a disco con snapshot_id compartido
  - Coordinar la pausa forzosa del sistema para guardados profundos
  - Gestionar elementos globales (ciclo día-noche, ciclo lunar, etc.)

Variables de entorno relevantes:
  GRID_WIDTH, GRID_HEIGHT, SECTOR_SIZE
  GESTOR_MUNDO_HOST, GESTOR_MUNDO_WORKERS
  TICK_TIMEOUT_MS, TICKS_ANTES_DE_DORMIR
  UNITY_FRAME_EVERY_N_TICKS
  MAX_VISION_DISTANCE, SOUND_MAP_CELL_SIZE
  SNAPSHOT_DIR, SNAPSHOT_INTERVAL_TICKS
  DEEP_SAVE_INTERVAL_TICKS
"""

import asyncio
import datetime
import logging
import math
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional

import grpc
from numpy import uint64

from typing import Optional

# Imports generados por protoc — ajustar paths según Proto_Generated
from Config.settings import DEFAULT_TICK_RATE
from Core.Entities.Elementos.elemento import Elemento
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


# ─────────────────────────────────────────────────────────────
#  Tipos internos
# ─────────────────────────────────────────────────────────────


class SystemState(Enum):
    RUNNING = auto()
    PAUSING = auto()  # pausa en progreso — esperando ACKs
    PAUSED = auto()  # completamente congelado
    RESUMING = auto()


@dataclass
class SectorInfo:
    """Metadata de un sector conocido por el Gestor_Mundo."""

    col: int
    row: int
    address: str  # host:port del proceso de sector
    mode: SectorMode = SectorMode.INACTIVO
    channel: Optional[grpc.aio.Channel] = field(default=None, repr=False)
    stub: Optional[object] = field(default=None, repr=False)
    ticks_sin_actividad: int = 0  # para anti-thrashing


@dataclass
class ActionResult:
    __slots__ = ("ok", "payload", "error", "world_tick")

    def __init__(self, ok, payload, error, world_tick=0):
        self.ok = ok
        self.payload = payload
        self.error = error
        self.world_tick = world_tick

    def __repr__(self):
        return f"ActionResult(ok={self.ok}, error={self.error!r})"


# ─────────────────────────────────────────────────────────────
#  Elementos globales base
# ─────────────────────────────────────────────────────────────


class ElementoGlobal:
    """Clase base para elementos globales (ciclos temporales, etc.)."""

    def tick(self, tick_id: int) -> dict:
        """Avanza el estado un tick. Devuelve dict con cambios para sectores."""
        raise NotImplementedError

    def to_snapshot(self) -> dict:
        raise NotImplementedError

    @classmethod
    def from_snapshot(cls, data: dict) -> "ElementoGlobal":
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────
#  GestorMundo
# ─────────────────────────────────────────────────────────────


class GestorMundo:

    def __init__(self):

        # ─────────────────────────────────────────────────────────────
        #  Configuración desde entorno
        # ─────────────────────────────────────────────────────────────

        self.GRID_WIDTH = int(os.getenv("GRID_WIDTH", 1000))
        self.GRID_HEIGHT = int(os.getenv("GRID_HEIGHT", 1000))
        self.SECTOR_SIZE = int(os.getenv("SECTOR_SIZE", 100))
        self.MAX_VISION_DISTANCE = int(os.getenv("MAX_VISION_DISTANCE", 50))
        self.SOUND_MAP_CELL_SIZE = int(os.getenv("SOUND_MAP_CELL_SIZE", 10))
        self.TICK_TIMEOUT_MS = int(os.getenv("TICK_TIMEOUT_MS", 500))
        self.TICKS_ANTES_DE_DORMIR = int(os.getenv("TICKS_ANTES_DE_DORMIR", 10))
        self.UNITY_FRAME_EVERY_N_TICKS = int(os.getenv("UNITY_FRAME_EVERY_N_TICKS", 1))
        self.SNAPSHOT_INTERVAL_TICKS = int(os.getenv("SNAPSHOT_INTERVAL_TICKS", 100))
        self.DEEP_SAVE_INTERVAL_TICKS = int(os.getenv("DEEP_SAVE_INTERVAL_TICKS", 500))
        self.SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "/data/snapshots"))
        self.GESTOR_BOTS_ADDRESS = os.getenv("GESTOR_BOTS_ADDRESS", "localhost:50051")

        self.COLS = math.ceil(self.GRID_WIDTH / self.SECTOR_SIZE)
        self.ROWS = math.ceil(self.GRID_HEIGHT / self.SECTOR_SIZE)

        # Sectores indexados por (col, row)
        self._sectores: dict[tuple[int, int], SectorInfo] = {}

        # Estado gold de celdas: dict[tuple[x,y], list[int64]] (posicion, lista de id_elemento)
        # Solo celdas no vacías. Cargado desde snapshot o construido al inicio.
        self._gold_cells: dict[tuple[int, int], list[uint64]] = {}

        # id → elemento (incluye bots)
        self._elements: dict[uint64, Elemento] = {}

        # bot_id → posición (fuente de verdad exclusiva)
        self._bot_positions: dict[str, tuple[int, int]] = {}

        # Control de tick
        self._tick_id: uint64 = 0
        self._snapshot_id: str = ""

        # Control de sistema
        self._state: SystemState = SystemState.RUNNING
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()  # set = puede correr; clear = pausado
        self._tick_rate: int = DEFAULT_TICK_RATE
        self._tick_interval: float = 0.0  # calculado desde _tick_rate

        # Canal hacia Gestor_Bots
        self._bots_channel: Optional[grpc.aio.Channel] = None
        self._bots_stub = None

        # Elementos globales
        self._elementos_globales: dict[uint64, ElementoGlobal] = {
            # Añadir más elementos globales aquí
        }

        # Lock para operaciones sobre estado gold
        self._gold_lock: asyncio.Lock = asyncio.Lock()

        self._active_events: dict[str, Any] = {}
        self._speed_factor: float = 1.0

        # sonidos
        self._pending_sounds = {}

    # ─────────────────────────────────────────────────────────────
    #  Deteccion si hay cambios en el delta
    # ─────────────────────────────────────────────────────────────
    def _delta_tiene_actividad(self, delta) -> bool:
        """
        Determina si un delta de sector contiene actividad real.
        Usado por el anti-thrashing para decidir si resetear ticks_sin_actividad.
        Centraliza el criterio — añadir aquí nuevos tipos de actividad cuando aparezcan.
        """
        return bool(delta.changed_cells or delta.outgoing_bots or delta.emitted_sounds)

    # ─────────────────────────────────────────────
    #  Arranque
    # ─────────────────────────────────────────────

    async def start(self, fresh: bool = False) -> None:
        """
        Arranca el gestor.
        fresh=True  → partida nueva, crea y registra todos los sectores.
        fresh=False → restauración desde último snapshot disponible.
        """
        self.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

        self._bots_channel = grpc.aio.insecure_channel(self.GESTOR_BOTS_ADDRESS)
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
        """Partida nueva: crea todos los sectores y carga el gold inicial vacío."""
        logger.info("Inicio limpio. Creando %d×%d sectores.", self.COLS, self.ROWS)
        for col in range(self.COLS):
            for row in range(self.ROWS):
                address = self._sector_address(col, row)
                info = SectorInfo(col=col, row=row, address=address)
                self._sectores[(col, row)] = info
                await self._connect_sector(info)
                await self._set_sector_mode(info, SectorMode.INACTIVO)

    async def _restore_from_snapshot(self) -> None:
        """Restaura desde el último snapshot disponible en disco."""
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

        # Restaurar elementos globales
        # TODO: hacer el registro de clases dinámico cuando haya más elementos
        eg_data = data.get("elementos_globales", {})
        for elem in self._elementos_globales.values():
            name = elem.__class__.__name__
            if name in eg_data:
                elem.__dict__.update(elem.from_snapshot(eg_data[name]).__dict__)

        # Restaurar sectores
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

        # Restaurar gold cells
        self._gold_cells = {
            tuple(map(int, k.split(","))): bytes.fromhex(v)
            for k, v in data.get("gold_cells", {}).items()
        }

        # Enviar estado gold a cada sector
        await self._distribute_gold_to_sectors()

    # ─────────────────────────────────────────────
    #  Ciclo principal de ticks
    # ─────────────────────────────────────────────

    async def run_loop(self) -> None:
        """Bucle principal de ticks. Correr como tarea asyncio."""
        while True:
            # Esperar si el sistema está pausado
            await self._pause_event.wait()

            t0 = time.monotonic()
            await self._run_tick()
            elapsed = time.monotonic() - t0

            self._tick_id += 1

            # Snapshots periódicos
            if self._tick_id % self.SNAPSHOT_INTERVAL_TICKS == 0:
                asyncio.create_task(self._save_snapshot())

            # Guardado profundo (pausa forzosa)
            if self._tick_id % self.DEEP_SAVE_INTERVAL_TICKS == 0:
                await self._deep_save()

            logger.debug("Tick %d completado en %.3fs", self._tick_id, elapsed)
            # Respetar cadencia deseada — si elapsed ya superó el intervalo, no esperar
            if self._tick_interval > 0:
                sobrante = self._tick_interval - elapsed
                if sobrante > 0:
                    await asyncio.sleep(sobrante)

    async def _run_tick(self) -> None:
        """Ejecuta las tres fases de un tick."""
        await self._fase_0()
        await self._fase_1()
        await self._fase_2()

    # ─────────────────────────────────────────────
    #  FASE 0 — Preparación
    # ─────────────────────────────────────────────

    async def _fase_0(self) -> None:
        """
        Distribuye a sectores ACTIVOS y DORMIDOS:
          - Ghost zones (celdas borde de sectores vecinos)
          - Sonidos cross-border
          - Bots migrados del tick anterior
        """
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
            # Los bots migrados se envían en _fase_2 del tick anterior;
            # aquí se reenvía si hubo bots en tránsito que no llegaron.

        await asyncio.gather(*tareas, return_exceptions=True)

    async def _enviar_ghost_zone(self, sector: SectorInfo) -> None:
        ghost_cells = self._calcular_ghost_zone(sector)
        if not ghost_cells:
            return
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

    async def _enviar_sonidos(self, sector: SectorInfo) -> None:
        # Los sonidos del tick anterior se acumulan en _pending_sounds
        # durante _fase_2. Aquí se distribuyen.
        sounds = self._pending_sounds.get((sector.col, sector.row), [])
        if not sounds:
            return
        req = sector_pb.SetSoundsRequest(
            tick_id=self._tick_id,
            sounds=sounds,
        )
        try:
            resp = await sector.stub.SetSounds(req)
            if not resp.ok:
                logger.warning(
                    "SetSounds falló en (%d,%d): %s", sector.col, sector.row, resp.error
                )
        except grpc.aio.AioRpcError as e:
            logger.error("gRPC error SetSounds (%d,%d): %s", sector.col, sector.row, e)

    # ─────────────────────────────────────────────
    #  FASE 1 — Computación paralela
    # ─────────────────────────────────────────────

    async def _fase_1(self) -> None:
        """Ordena a todos los sectores ACTIVOS que computen en paralelo."""
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
            elif resultado.timed_out:
                logger.warning(
                    "Sector (%d,%d) no terminó a tiempo (tick %d)",
                    sector.col,
                    sector.row,
                    self._tick_id,
                )

    async def _start_tick_sector(self, sector: SectorInfo):
        req = sector_pb.StartTickRequest(
            tick_id=self._tick_id,
            timeout_ms=self.TICK_TIMEOUT_MS,
        )
        return await sector.stub.StartTick(req)

    # ─────────────────────────────────────────────
    #  FASE 2 — Consolidación
    # ─────────────────────────────────────────────

    async def _fase_2(self) -> None:
        """
        Recoge deltas de sectores ACTIVOS, consolida el estado gold,
        resuelve migraciones, procesa sonidos para el siguiente tick,
        envía frame a Unity cada N ticks, señaliza reset de presupuestos.
        """
        activos = [s for s in self._sectores.values() if s.mode == SectorMode.ACTIVO]

        # Recoger deltas en paralelo
        tareas = [self._get_delta_sector(s) for s in activos]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)

        # Acumuladores para este tick
        self._pending_sounds: dict[tuple[int, int], list] = {}
        bots_migrando: list[tuple[SectorInfo, sector_pb.MigratingBot]] = []

        async with self._gold_lock:
            for sector, resultado in zip(activos, resultados):
                if isinstance(resultado, Exception):
                    logger.error(
                        "Error en GetDelta sector (%d,%d): %s",
                        sector.col,
                        sector.row,
                        resultado,
                    )
                    continue
                if not resultado.ok:
                    logger.warning(
                        "GetDelta falló en (%d,%d): %s",
                        sector.col,
                        sector.row,
                        resultado.error,
                    )
                    continue

                # Actualizar gold con celdas cambiadas
                for cell in resultado.changed_cells:
                    key = (cell.pos.x, cell.pos.y)
                    if cell.element:
                        self._gold_cells[key] = cell.element
                    else:
                        self._gold_cells.pop(key, None)

                # Acumular bots que migran
                for bot in resultado.outgoing_bots:
                    bots_migrando.append((sector, bot))

                # Procesar sonidos emitidos → distribuir a sectores afectados
                for sound in resultado.emitted_sounds:
                    self._distribuir_sonido(sound)

                # Actualizar contador anti-thrashing
                if self._delta_tiene_actividad(resultado):
                    sector.ticks_sin_actividad = 0

            # Resolver migraciones
            await self._resolver_migraciones(bots_migrando)

            # Actualizar modos de sector (anti-thrashing)
            await self._actualizar_modos_sector()

            # Avanzar elementos globales
            cambios_globales = {}
            for elem in self._elementos_globales:
                cambios_globales.update(elem.tick(self._tick_id))
            # TODO: distribuir cambios_globales a sectores que lo necesiten

        # Enviar frame a Unity
        if self._tick_id % self.UNITY_FRAME_EVERY_N_TICKS == 0:
            await self._enviar_frame_unity()

        # Señalizar reset de presupuestos al Gestor_Bots
        await self._reset_budgets()

    async def _get_delta_sector(self, sector: SectorInfo):
        req = sector_pb.GetDeltaRequest(tick_id=self._tick_id)
        return await sector.stub.GetDelta(req)

    # ─────────────────────────────────────────────
    #  Migraciones
    # ─────────────────────────────────────────────

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
                # Activar el sector destino
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

    # ─────────────────────────────────────────────
    #  Sonidos cross-border
    # ─────────────────────────────────────────────

    def _distribuir_sonido(self, sound: common_pb.SoundEvent) -> None:
        """
        Determina qué sectores reciben este sonido usando el mapa low-res
        y los acumula en _pending_sounds para la FASE 0 del siguiente tick.
        """
        # Coordenadas en el mapa low-res
        lx = sound.origin.x // self.SOUND_MAP_CELL_SIZE
        ly = sound.origin.y // self.SOUND_MAP_CELL_SIZE

        # Radio máximo en celdas low-res
        from Core.Mundo.mapa_config import MAX_SOUND_DISTANCE

        radio_lr = math.ceil(MAX_SOUND_DISTANCE / self.SOUND_MAP_CELL_SIZE)

        for col in range(self.COLS):
            for row in range(self.ROWS):
                sx = (col * self.SECTOR_SIZE) // self.SOUND_MAP_CELL_SIZE
                sy = (row * self.SECTOR_SIZE) // self.SOUND_MAP_CELL_SIZE
                if abs(sx - lx) <= radio_lr and abs(sy - ly) <= radio_lr:
                    key = (col, row)
                    self._pending_sounds.setdefault(key, []).append(sound)

    # ─────────────────────────────────────────────
    #  Modos de sector y anti-thrashing
    # ─────────────────────────────────────────────

    async def _actualizar_modos_sector(self) -> None:
        """
        Pone en DORMIDO los sectores ACTIVOS sin actividad reciente,
        y activa los vecinos de cualquier sector ACTIVO.
        """
        for info in self._sectores.values():
            if info.mode == SectorMode.ACTIVO:
                info.ticks_sin_actividad += 1
                if info.ticks_sin_actividad >= self.TICKS_ANTES_DE_DORMIR:
                    await self._set_sector_mode(info, SectorMode.DORMIDO)
                else:
                    # Sus vecinos deben estar al menos DORMIDOS
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
        """
        Llamado cuando un bot nace o entra en un sector inactivo.
        Encola la activación para el próximo tick.
        """
        info = self._sector_para_posicion(x, y)
        if info and info.mode == SectorMode.INACTIVO:
            asyncio.create_task(self._set_sector_mode(info, SectorMode.ACTIVO))

    # ─────────────────────────────────────────────
    #  Sistema de pausa / congelación
    # ─────────────────────────────────────────────

    async def freeze(self) -> None:
        """
        Pausa forzosa inmediata del sistema completo.
        Bloquea el bucle de ticks y ordena a Gestor_Bots congelar todos los HVs.
        """
        if self._state != SystemState.RUNNING:
            return

        logger.info("FREEZE iniciado (tick %d)", self._tick_id)
        self._state = SystemState.PAUSING
        self._pause_event.clear()

        # Ordenar a Gestor_Bots que congele todos los HVs
        try:
            await self._bots_stub.FreezeAll(bots_pb.FreezeAllRequest())
        except grpc.aio.AioRpcError as e:
            logger.error("Error al congelar Gestor_Bots: %s", e)

        # Ordenar a todos los sectores activos que pausen
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
        """Reanuda el sistema tras una pausa."""
        if self._state != SystemState.PAUSED:
            return

        logger.info("RESUME (tick %d)", self._tick_id)
        self._state = SystemState.RESUMING

        # Restaurar modos de sector según estado gold
        await self._distribute_gold_to_sectors()

        # Ordenar a Gestor_Bots que reanude
        try:
            await self._bots_stub.ResumeAll(bots_pb.ResumeAllRequest())
        except grpc.aio.AioRpcError as e:
            logger.error("Error al reanudar Gestor_Bots: %s", e)

        self._state = SystemState.RUNNING
        self._pause_event.set()
        logger.info("Sistema reanudado.")

    async def set_tick_rate(self, ticks_per_second: int) -> None:
        """
        Cambia la cadencia del bucle en caliente.
        ticks_per_second <= 0 → sin límite (modo entrenar).
        """
        self._tick_rate = ticks_per_second
        self._tick_interval = (1.0 / ticks_per_second) if ticks_per_second > 0 else 0.0
        logger.info(
            "Cadencia de ticks cambiada a %s",
            "sin límite" if ticks_per_second <= 0 else f"{ticks_per_second}/s",
        )

    # ─────────────────────────────────────────────
    #  Snapshots
    # ─────────────────────────────────────────────

    async def _save_snapshot(self) -> None:
        """
        Guarda el estado gold del Gestor_Mundo a disco.
        No pausa el sistema — solo copia el gold en un momento dado.
        """
        import json

        snapshot_id = f"{self._tick_id:010d}"
        path = self.SNAPSHOT_DIR / f"mundo_{snapshot_id}.json"

        async with self._gold_lock:
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
                "gold_cells": {
                    f"{x},{y}": v.hex() for (x, y), v in self._gold_cells.items()
                },
                "elementos_globales": {
                    elem.__class__.__name__: elem.to_snapshot()
                    for elem in self._elementos_globales.values()
                },
            }

        path.write_text(__import__("json").dumps(data))
        self._snapshot_id = snapshot_id
        logger.info("Snapshot guardado: %s", path)

    async def _deep_save(self) -> None:
        """
        Guardado profundo: pausa el sistema, guarda snapshot coordinado
        (mundo + sectores + bots con el mismo snapshot_id), reanuda.
        """
        logger.info("Guardado profundo iniciado (tick %d)", self._tick_id)
        await self.freeze()
        try:
            snapshot_id = f"{self._tick_id:010d}_deep"
            self._snapshot_id = snapshot_id
            await self._save_snapshot()
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
            await self.resume()

    def _latest_snapshot_path(self) -> Optional[Path]:
        """Devuelve el path del snapshot más reciente en SNAPSHOT_DIR."""
        snapshots = sorted(self.SNAPSHOT_DIR.glob("mundo_*.json"))
        return snapshots[-1] if snapshots else None

    # ─────────────────────────────────────────────
    #  Distribución del gold a sectores
    # ─────────────────────────────────────────────

    async def _distribute_gold_to_sectors(self) -> None:
        """Envía el estado gold completo a cada sector (arranque o restauración)."""
        tareas = []
        for info in self._sectores.values():
            if info.stub is not None:
                tareas.append(self._load_sector_state(info))
        await asyncio.gather(*tareas, return_exceptions=True)

    async def _load_sector_state(self, info: SectorInfo) -> None:
        cells = self._celdas_de_sector(info)
        req = sector_pb.LoadStateRequest(cells=cells)
        try:
            resp = await info.stub.LoadState(req)
            if not resp.ok:
                logger.warning(
                    "LoadState falló en (%d,%d): %s", info.col, info.row, resp.error
                )
        except grpc.aio.AioRpcError as e:
            logger.error("gRPC error LoadState (%d,%d): %s", info.col, info.row, e)

    # ─────────────────────────────────────────────
    #  Unity
    # ─────────────────────────────────────────────

    async def _enviar_frame_unity(self) -> None:
        """
        TODO: implementar con el protocolo de Unity decidido.
        Por ahora no-op.
        """
        pass

    # ─────────────────────────────────────────────
    #  Gestor_Bots — reset de presupuestos
    # ─────────────────────────────────────────────

    async def _reset_budgets(self) -> None:
        try:
            await self._bots_stub.ResetBudgets(bots_pb.ResetBudgetsRequest())
        except grpc.aio.AioRpcError as e:
            logger.error("Error al resetear presupuestos: %s", e)

    # ─────────────────────────────────────────────
    #  Helpers de geometría
    # ─────────────────────────────────────────────

    def get_celda(self, x: int, y: int) -> Optional[bytes]:
        """
        Devuelve el contenido serializado de la celda (x, y), o None si está vacía.
        Abstrae el sistema de sectores — el caller no necesita saber en qué sector está.
        """
        return self._gold_cells.get((x, y))

    async def handle_action(
        self, bot_id: uint64, action_type: str, payload: bytes
    ) -> ActionResult:
        from Infraestructura.Gestores.Mundo.api_acciones import ACCIONES, AccionContext

        entrada = ACCIONES.get(action_type)
        if entrada is None:
            logger.warning(
                "handle_action: acción desconocida '%s' (bot %s)", action_type, bot_id
            )
            return ActionResult(ok=False, error=f"Acción desconocida: {action_type}")

        fn = entrada.get("funcion")
        if fn is None:
            logger.warning(
                "handle_action: acción '%s' no tiene funcion (bot %s)",
                action_type,
                bot_id,
            )
            return ActionResult(
                ok=False, error=f"Acción '{action_type}' no ejecutable por el Mundo."
            )

        ctx = AccionContext(
            bot_id=bot_id,
            payload=payload,
            gold_cells=self._gold_cells,
            elements=self._elements,
            bot_positions=self._bot_positions,
        )

        try:
            return await fn(ctx)
        except Exception as exc:
            logger.error(
                "Error en handle_action '%s' para bot %s: %s", action_type, bot_id, exc
            )
            return ActionResult(ok=False, error=str(exc))

    def _sector_para_posicion(self, x: int, y: int) -> Optional[SectorInfo]:
        col = x // self.SECTOR_SIZE
        row = y // self.SECTOR_SIZE
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

    def _celdas_de_sector(self, info: SectorInfo) -> list:
        """Extrae del gold las celdas que pertenecen a este sector."""
        x0 = info.col * self.SECTOR_SIZE
        y0 = info.row * self.SECTOR_SIZE
        x1 = x0 + self.SECTOR_SIZE
        y1 = y0 + self.SECTOR_SIZE
        result = []
        for (x, y), element in self._gold_cells.items():
            if x0 <= x < x1 and y0 <= y < y1:
                result.append(
                    common_pb.Cell(
                        pos=common_pb.Position(x=x, y=y),
                        element=element,
                    )
                )
        return result

    def _calcular_ghost_zone(self, info: SectorInfo) -> list:
        """
        Devuelve las celdas del gold que están en la ghost zone del sector:
        celdas de sectores vecinos dentro de MAX_VISION_DISTANCE del borde.
        """
        x0 = info.col * self.SECTOR_SIZE
        y0 = info.row * self.SECTOR_SIZE
        x1 = x0 + self.SECTOR_SIZE
        y1 = y0 + self.SECTOR_SIZE
        gx0 = x0 - self.MAX_VISION_DISTANCE
        gy0 = y0 - self.MAX_VISION_DISTANCE
        gx1 = x1 + self.MAX_VISION_DISTANCE
        gy1 = y1 + self.MAX_VISION_DISTANCE

        result = []
        for (x, y), element in self._gold_cells.items():
            # Celdas fuera del sector propio pero dentro del borde ampliado
            if (
                gx0 <= x < gx1
                and gy0 <= y < gy1
                and not (x0 <= x < x1 and y0 <= y < y1)
            ):
                result.append(
                    common_pb.Cell(
                        pos=common_pb.Position(x=x, y=y),
                        element=element,
                    )
                )
        return result

    # ─────────────────────────────────────────────
    #  Conexiones gRPC a sectores
    # ─────────────────────────────────────────────

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
