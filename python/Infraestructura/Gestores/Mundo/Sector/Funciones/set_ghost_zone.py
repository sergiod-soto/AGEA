# Gestores/Mundo/Sector/funciones/set_ghost_zone.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import sector_service_pb2 as pb
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
import logging

logger = logging.getLogger(__name__)
NAME = "SetGhostZone"

async def handle(sector: Sector, request, context) -> pb.SetGhostZoneResponse:
    try:
        sector.set_ghost_zone(tick_id=request.tick_id, ghost_cells=list(request.ghost_cells))
        return pb.SetGhostZoneResponse(ok=True)
    except Exception as e:
        logger.exception("Error en SetGhostZone")
        return pb.SetGhostZoneResponse(ok=False, error=str(e))