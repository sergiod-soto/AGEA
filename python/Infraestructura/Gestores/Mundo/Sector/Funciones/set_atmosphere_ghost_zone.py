# Gestores/Mundo/Sector/funciones/set_atmosphere_ghost_zone.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as pb,
)
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
import logging

logger = logging.getLogger(__name__)
NAME = "SetAtmosphereGhostZone"


async def handle(sector: Sector, request, context) -> pb.SetAtmosphereGhostZoneResponse:
    try:
        sector.set_ghost_zone_atmosfera(
            tick_id=request.tick_id, ghost_cells=list(request.ghost_cells)
        )
        return pb.SetAtmosphereGhostZoneResponse(ok=True)
    except Exception as e:
        logger.exception("Error en SetAtmosphereGhostZone")
        return pb.SetAtmosphereGhostZoneResponse(ok=False, error=str(e))
