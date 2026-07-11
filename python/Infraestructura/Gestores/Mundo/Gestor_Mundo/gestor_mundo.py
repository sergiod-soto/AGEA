# Infraestructura/Gestores/Mundo/Gestor_Mundo/gestor_mundo.py
"""
gestor_mundo.py
---------------
Gestor central del MECANISMO del mundo (ya no de su estado).

Responsabilidades tras el refactor a Logica_Mundo:
  - Ejecutar el ciclo de tick en tres fases (FASE 0 / 1 / 2)
  - Gestionar el ciclo de vida de los sectores (crear, registrar, cambiar modo)
  - Emitir snapshots periódicos propios (topología de sectores) y pedir a
    Logica_Mundo que guarde el suyo con el mismo snapshot_id compartido
  - Coordinar la pausa forzosa del sistema para guardados profundos

Lo que YA NO hace (migrado a Logica_Mundo):
  - Mantener _gold_cells / _elements / _bot_positions
  - Resolver acciones de bots (handle_action)
  - Avanzar elementos globales (ciclo día-noche, lunar, etc.)
  - Gestionar eventos globales

Para todo lo anterior, este módulo habla con Logica_Mundo a través de
un cliente gRPC (self._logica_client) — ver logica_mundo_client.py
(pendiente de escribir).

Variables de entorno relevantes:
  GRID_WIDTH, GRID_HEIGHT, SECTOR_SIZE
  GESTOR_MUNDO_HOST, GESTOR_MUNDO_WORKERS
  GESTOR_BOTS_ADDRESS, LOGICA_MUNDO_ADDRESS
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
from typing import Optional

import grpc
from numpy import uint64

# Imports generados por protoc — ajustar paths según Proto_Generated
from Config.settings import DEFAULT_TICK_RATE
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


# ─────────────────────────────────────────────────────────────
#  GestorMundo
# ─────────────────────────────────────────────────────────────


class GestorMundo:

    def __init__(self, logica_client):
        """
        logica_client : cliente gRPC hacia Logica_Mundo (ver
                        logica_mundo_client.py, pendiente). Se inyecta
                        en vez de construirse aquí para poder testear
                        GestorMundo con un doble sin infraestructura real
                        — mismo patrón que ya usa ShutdownCoordinator.
        """
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

        # Cliente hacia Logica_Mundo — única fuente de verdad del estado
        # gold. Gestor_Mundo ya no mantiene copia propia.
        self._logica_client = logica_client

        # Control de tick
        self._tick_id: uint64 = 0
        self._snapshot_id: str = ""

        # Control de sistema
        self._state: SystemState = SystemState.RUNNING
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()  # set = puede correr; clear = pausado
        self._tick_rate: int = DEFAULT_TICK_RATE
        self._tick_interval: float = 0.0  # calculado desde _tick_rate

        # Canal hacia Gestor_Bots (para FreezeAll/ResumeAll/ResetBudgets —
        # órdenes administrativas que siguen coordinándose desde aquí,
        # ya que son parte del ciclo de tick, no del estado del mundo)
        self._bots_channel: Optional[grpc.aio.Channel] = None
        self._bots_stub = None

        # Lock — ya no protege _gold_cells (que no existe aquí), pero se
        # mantiene para serializar la consolidación de _fase_2 frente a
        # freeze()/save_snapshot() concurrentes, igual que antes.
        self._consolidacion_lock: asyncio.Lock = asyncio.Lock()

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
        """Partida nueva: crea todos los sectores. El gold inicial vacío
        ya existe por defecto en Logica_Mundo (no hace falta inicializarlo
        aquí — es su propio estado, no el nuestro)."""
        logger.info("Inicio limpio. Creando %d×%d sectores.", self.COLS, self.ROWS)
        for col in range(self.COLS):
            for row in range(self.ROWS):
                address = self._sector_address(col, row)
                info = SectorInfo(col=col, row=row, address=address)
                self._sectores[(col, row)] = info
                await self._connect_sector(info)
                await self._set_sector_mode(info, SectorMode.INACTIVO)

    async def _restore_from_snapshot(self) -> None:
        """
        Restaura desde el último snapshot disponible en disco.

        Solo restaura AQUÍ la topología propia (sectores, tick_id).
        El estado gold se restaura pidiendo a Logica_Mundo que cargue
        su propio snapshot con el mismo snapshot_id — ambos snapshots
        se guardaron juntos (ver _save_snapshot), así que están
        garantizados a corresponder al mismo instante.
        """
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

        # Restaurar sectores (topología propia)
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

        # Pedir a Logica_Mundo que restaure su estado con el mismo id
        await self._logica_client.load_state(self._snapshot_id)

        # Enviar estado gold (ahora en Logica_Mundo) a cada sector
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
        """
        Pide a Logica_Mundo las celdas del borde ampliado del sector
        (excluyendo la región propia) y se las envía como ghost zone.

        Antes esto se resolvía leyendo self._gold_cells directamente;
        ahora es una única llamada RPC por sector por tick — coste
        aceptable porque escala con nº de sectores, no con nº de bots
        (ver discusión de escalabilidad).
        """
        ghost_cells = await self._calcular_ghost_zone(sector)
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
        Recoge deltas de sectores ACTIVOS, entrega las celdas cambiadas
        a Logica_Mundo para que consolide su estado, resuelve
        migraciones, procesa sonidos para el siguiente tick, envía
        frame a Unity cada N ticks, señaliza reset de presupuestos.
        """
        activos = [s for s in self._sectores.values() if s.mode == SectorMode.ACTIVO]

        # Recoger deltas en paralelo
        tareas = [self._get_delta_sector(s) for s in activos]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)

        # Acumuladores para este tick
        self._pending_sounds: dict[tuple[int, int], list] = {}
        bots_migrando: list[tuple[SectorInfo, sector_pb.MigratingBot]] = []

        # Todas las celdas cambiadas de todos los sectores de este tick,
        # para entregarlas a Logica_Mundo en una sola llamada batcheada
        # en vez de una llamada por sector — reduce round-trips.
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
                    continue
                if not resultado.ok:
                    logger.warning(
                        "GetDelta falló en (%d,%d): %s",
                        sector.col,
                        sector.row,
                        resultado.error,
                    )
                    continue

                # Acumular celdas cambiadas — se entregan a Logica_Mundo
                # tal cual (proto Cell), sin interpretarlas aquí.
                celdas_cambiadas.extend(resultado.changed_cells)

                # Acumular bots que migran
                for bot in resultado.outgoing_bots:
                    bots_migrando.append((sector, bot))

                # Procesar sonidos emitidos → distribuir a sectores afectados
                for sound in resultado.emitted_sounds:
                    self._distribuir_sonido(sound)

                # Actualizar contador anti-thrashing
                if self._delta_tiene_actividad(resultado):
                    sector.ticks_sin_actividad = 0

            # Entregar las celdas cambiadas a Logica_Mundo para que
            # consolide su estado (sustituye la escritura directa en
            # self._gold_cells que hacía la versión anterior).
            if celdas_cambiadas:
                await self._logica_client.actualizar_celdas(celdas_cambiadas)

            # Resolver migraciones
            await self._resolver_migraciones(bots_migrando)

            # Actualizar modos de sector (anti-thrashing)
            await self._actualizar_modos_sector()

            # Avanzar elementos globales — ahora vive en Logica_Mundo,
            # que devuelve los cambios agregados de este tick.
            cambios_globales = await self._logica_client.avanzar_elementos_globales(
                self._tick_id
            )
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

        No requiere el estado gold — es geometría pura sobre coordenadas
        de sector, por eso se queda aquí (mecánica de tick) y no en
        Logica_Mundo.
        """
        lx = sound.origin.x // self.SOUND_MAP_CELL_SIZE
        ly = sound.origin.y // self.SOUND_MAP_CELL_SIZE

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
        """Reanuda el sistema tras una pausa."""
        if self._state != SystemState.PAUSED:
            return

        logger.info("RESUME (tick %d)", self._tick_id)
        self._state = SystemState.RESUMING

        # Restaurar modos de sector con el gold actual (en Logica_Mundo)
        await self._distribute_gold_to_sectors()

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
        Guarda la topología propia (sectores, tick_id) a disco, y pide a
        Logica_Mundo que guarde su estado con el MISMO snapshot_id —
        así ambos snapshots quedan correlacionados y se pueden restaurar
        juntos sin ambigüedad.
        """
        import json

        snapshot_id = f"{self._tick_id:010d}"
        path = self.SNAPSHOT_DIR / f"mundo_{snapshot_id}.json"

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

        path.write_text(json.dumps(data))

        # Logica_Mundo guarda su propio estado (gold, IDs, eventos...)
        # con el mismo identificador.
        await self._logica_client.save_snapshot(snapshot_id)

        self._snapshot_id = snapshot_id
        logger.info("Snapshot guardado: %s", path)

    async def _deep_save(self) -> None:
        """
        Guardado profundo: pausa el sistema, guarda snapshot coordinado
        (mundo + logica_mundo + sectores + bots con el mismo snapshot_id), reanuda.

        Importante: si el sistema ya estaba pausado por el usuario ANTES de
        que saltara este guardado automático, no debemos reanudarlo al
        terminar — solo restauramos el estado que había antes de que
        _deep_save tomara el control.
        """
        logger.info("Guardado profundo iniciado (tick %d)", self._tick_id)

        estaba_corriendo = self._state == SystemState.RUNNING

        await self.freeze()
        try:
            snapshot_id = f"{self._tick_id:010d}_deep"
            self._snapshot_id = snapshot_id

            # _save_snapshot ya incluye la llamada a Logica_Mundo, pero
            # aquí forzamos el snapshot_id "_deep" en vez del periódico —
            # por eso se guarda inline en vez de reusar _save_snapshot().
            import json

            path = self.SNAPSHOT_DIR / f"mundo_{snapshot_id}.json"
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
            path.write_text(json.dumps(data))
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
        """Devuelve el path del snapshot más reciente en SNAPSHOT_DIR."""
        snapshots = sorted(self.SNAPSHOT_DIR.glob("mundo_*.json"))
        return snapshots[-1] if snapshots else None

    # ─────────────────────────────────────────────
    #  Distribución del gold a sectores
    # ─────────────────────────────────────────────

    async def _distribute_gold_to_sectors(self) -> None:
        """Envía el estado gold completo (obtenido de Logica_Mundo) a cada sector."""
        tareas = []
        for info in self._sectores.values():
            if info.stub is not None:
                tareas.append(self._load_sector_state(info))
        await asyncio.gather(*tareas, return_exceptions=True)

    async def _load_sector_state(self, info: SectorInfo) -> None:
        """
        Pide a Logica_Mundo las celdas de la región de este sector
        (sin exclusión — queremos todo el rectángulo propio) y se las
        envía. Antes se leía self._gold_cells directamente.
        """
        x0 = info.col * self.SECTOR_SIZE
        y0 = info.row * self.SECTOR_SIZE
        x1 = x0 + self.SECTOR_SIZE
        y1 = y0 + self.SECTOR_SIZE

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

    # ─────────────────────────────────────────────
    #  Unity
    # ─────────────────────────────────────────────

    async def _enviar_frame_unity(self) -> None:
        """
        Ya no aplica aquí — la representación para Unity la resuelve
        Logica_Mundo a petición de Comunicacion_Remoto/Vista_Foco, no
        empujada por Gestor_Mundo en cada tick. Se mantiene el hook por
        si en el futuro hace falta notificar "hay un frame nuevo
        disponible" sin enviar los datos en sí.
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

    async def _calcular_ghost_zone(self, info: SectorInfo) -> list:
        """
        Pide a Logica_Mundo las celdas del borde ampliado del sector,
        excluyendo la región propia — sustituye la lectura directa de
        self._gold_cells que hacía la versión anterior.
        """
        x0 = info.col * self.SECTOR_SIZE
        y0 = info.row * self.SECTOR_SIZE
        x1 = x0 + self.SECTOR_SIZE
        y1 = y0 + self.SECTOR_SIZE
        gx0 = x0 - self.MAX_VISION_DISTANCE
        gy0 = y0 - self.MAX_VISION_DISTANCE
        gx1 = x1 + self.MAX_VISION_DISTANCE
        gy1 = y1 + self.MAX_VISION_DISTANCE

        return await self._logica_client.obtener_celdas_en_region(
            min_pos=(gx0, gy0),
            max_pos=(gx1, gy1),
            excluir_min=(x0, y0),
            excluir_max=(x1, y1),
        )

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
