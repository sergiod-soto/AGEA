# Gestores/Mundo/Sector/funciones/load_state.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import sector_service_pb2 as pb
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
import logging

logger = logging.getLogger(__name__)
NAME = "LoadState"

async def handle(sector: Sector, request, context) -> pb.LoadStateResponse:
    try:
        sector.load_state(cells=list(request.cells), bots=list(request.bots))
        return pb.LoadStateResponse(ok=True)
    except Exception as e:
        logger.exception("Error en LoadState")
        return pb.LoadStateResponse(ok=False, error=str(e))