# Gestores/Mundo/Sector/funciones/start_tick.py
import asyncio
from Gestores.Transporte.Proto_Generated.Sectores import sector_service_pb2 as pb
from Gestores.Mundo.Sector.sector import Sector
import logging

logger = logging.getLogger(__name__)
NAME = "StartTick"

async def handle(sector: Sector, request, context) -> pb.StartTickResponse:
    try:
        loop = asyncio.get_running_loop()
        await asyncio.wait_for(
            loop.run_in_executor(None, sector.compute_tick, request.tick_id),
            timeout=request.timeout_ms / 1000,
        )
        return pb.StartTickResponse(ok=True, timed_out=False)
    except asyncio.TimeoutError:
        logger.warning(
            "Sector (%d,%d): tick %d excedió timeout (%d ms)",
            sector._col, sector._row, request.tick_id, request.timeout_ms,
        )
        return pb.StartTickResponse(ok=True, timed_out=True)
    except Exception as e:
        logger.exception("Error en StartTick")
        return pb.StartTickResponse(ok=False, timed_out=False)