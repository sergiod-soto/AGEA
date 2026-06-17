# Gestores/Mundo/Sector/funciones/get_state.py
from Gestores.Transporte.Proto_Generated.Sectores import sector_service_pb2 as pb
from Gestores.Mundo.Sector.sector import Sector
import logging

logger = logging.getLogger(__name__)
NAME = "GetState"

async def handle(sector: Sector, request, context) -> pb.GetStateResponse:
    try:
        cells, bots = sector.get_state()
        return pb.GetStateResponse(ok=True, cells=cells, bots=bots)
    except Exception as e:
        logger.exception("Error en GetState")
        return pb.GetStateResponse(ok=False, error=str(e))