# Infraestructura/Gestores/Mundo/Sector/Funciones/get_delta.py

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as pb,
)
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
import logging

logger = logging.getLogger(__name__)
NAME = "GetDelta"


async def handle(sector: Sector, request, context) -> pb.GetDeltaResponse:
    try:
        delta = sector.get_delta(request.tick_id)
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
            dead_bot_ids=delta.dead_bot_ids,
            emitted_sounds=delta.emitted_sounds,
            changed_atmosphere_cells=delta.changed_atmosphere_cells,
            movimientos_salientes=delta.movimientos_salientes,
        )
    except Exception as e:
        logger.exception("Error en GetDelta")
        return pb.GetDeltaResponse(ok=False, error=str(e), tick_id=request.tick_id)
