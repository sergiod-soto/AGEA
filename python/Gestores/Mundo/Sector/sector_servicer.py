"""
sector_servicer.py
------------------
Implementación gRPC del SectorService.
Recibe llamadas del Gestor_Mundo y las delega a Sector.

Carpeta: Gestores/Mundo/Sector/
"""

import asyncio
import logging

from Gestores.Transporte.Proto_Generated.Mundo import (
    sector_service_pb2 as pb,
    sector_service_pb2_grpc as pb_grpc,
)
from Gestores.Mundo.Sector.sector import Sector, SectorMode

logger = logging.getLogger(__name__)


class SectorServicer(pb_grpc.SectorServiceServicer):

    def __init__(self, sector: Sector) -> None:
        self._s = sector
        # Lock para serializar operaciones de FASE 0 concurrentes
        # (SetGhostZone, SetSounds, AddMigratingBot pueden llegar en paralelo)
        self._fase0_lock = asyncio.Lock()

    # ─────────────────────────────────────────
    #  Ciclo de vida
    # ─────────────────────────────────────────

    async def SetSectorMode(self, request, context):
        try:
            mode = SectorMode(request.mode)
            self._s.set_mode(mode)
            return pb.SetSectorModeResponse(ok=True)
        except ValueError as e:
            return pb.SetSectorModeResponse(ok=False, error=f"Modo desconocido: {e}")
        except Exception as e:
            logger.exception("Error en SetSectorMode")
            return pb.SetSectorModeResponse(ok=False, error=str(e))

    async def LoadState(self, request, context):
        try:
            self._s.load_state(
                cells=list(request.cells),
                bots=list(request.bots),
            )
            return pb.LoadStateResponse(ok=True)
        except Exception as e:
            logger.exception("Error en LoadState")
            return pb.LoadStateResponse(ok=False, error=str(e))

    async def GetState(self, request, context):
        try:
            cells, bots = self._s.get_state()
            return pb.GetStateResponse(ok=True, cells=cells, bots=bots)
        except Exception as e:
            logger.exception("Error en GetState")
            return pb.GetStateResponse(ok=False, error=str(e))

    # ─────────────────────────────────────────
    #  FASE 0 — Preparación del tick
    # ─────────────────────────────────────────

    async def SetGhostZone(self, request, context):
        try:
            async with self._fase0_lock:
                self._s.set_ghost_zone(
                    tick_id=request.tick_id,
                    ghost_cells=list(request.ghost_cells),
                )
            return pb.SetGhostZoneResponse(ok=True)
        except Exception as e:
            logger.exception("Error en SetGhostZone")
            return pb.SetGhostZoneResponse(ok=False, error=str(e))

    async def SetSounds(self, request, context):
        try:
            async with self._fase0_lock:
                self._s.set_sounds(
                    tick_id=request.tick_id,
                    sounds=list(request.sounds),
                )
            return pb.SetSoundsResponse(ok=True)
        except Exception as e:
            logger.exception("Error en SetSounds")
            return pb.SetSoundsResponse(ok=False, error=str(e))

    async def AddMigratingBot(self, request, context):
        try:
            async with self._fase0_lock:
                self._s.add_migrating_bot(
                    tick_id=request.tick_id,
                    bot=request.bot,
                )
            return pb.AddMigratingBotResponse(ok=True)
        except Exception as e:
            logger.exception("Error en AddMigratingBot")
            return pb.AddMigratingBotResponse(ok=False, error=str(e))

    # ─────────────────────────────────────────
    #  FASE 1 — Computación
    # ─────────────────────────────────────────

    async def StartTick(self, request, context):
        try:
            # Ejecutar compute_tick en un executor para no bloquear el event loop
            # si en el futuro hay operaciones CPU-bound dentro del tick
            loop = asyncio.get_running_loop()
            delta = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._s.compute_tick,
                    request.tick_id,
                ),
                timeout=request.timeout_ms / 1000,
            )
            return pb.StartTickResponse(ok=True, timed_out=False)
        except asyncio.TimeoutError:
            logger.warning(
                "Sector (%d,%d): tick %d excedió timeout (%d ms)",
                self._s._col,
                self._s._row,
                request.tick_id,
                request.timeout_ms,
            )
            return pb.StartTickResponse(ok=True, timed_out=True)
        except Exception as e:
            logger.exception("Error en StartTick")
            return pb.StartTickResponse(ok=False, timed_out=False)

    # ─────────────────────────────────────────
    #  FASE 2 — Consolidación
    # ─────────────────────────────────────────

    async def GetDelta(self, request, context):
        try:
            delta = self._s.get_delta(request.tick_id)
            if delta is None:
                return pb.GetDeltaResponse(
                    ok=False,
                    error=f"Delta no disponible para tick_id={request.tick_id}",
                    tick_id=request.tick_id,
                )
            return pb.GetDeltaResponse(
                ok=True,
                tick_id=delta.tick_id,
                changed_cells=delta.changed_cells,
                outgoing_bots=delta.outgoing_bots,
                dead_bot_ids=delta.dead_bot_ids,
                emitted_sounds=delta.emitted_sounds,
            )
        except Exception as e:
            logger.exception("Error en GetDelta")
            return pb.GetDeltaResponse(ok=False, error=str(e), tick_id=request.tick_id)

    # ─────────────────────────────────────────
    #  Snapshot
    # ─────────────────────────────────────────

    async def SaveSnapshot(self, request, context):
        try:
            await self._s.save_snapshot(snapshot_id=request.snapshot_id)
            return pb.SaveSnapshotResponse(
                ok=True,
                snapshot_id=request.snapshot_id,
            )
        except Exception as e:
            logger.exception("Error en SaveSnapshot")
            return pb.SaveSnapshotResponse(ok=False, error=str(e))
