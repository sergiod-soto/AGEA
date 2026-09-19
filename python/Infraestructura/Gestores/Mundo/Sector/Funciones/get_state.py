# Gestores/Mundo/Sector/funciones/get_state.py


from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as pb,
)
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
import logging

logger = logging.getLogger(__name__)
NAME = "GetState"


async def handle(sector: Sector, request, context) -> pb.GetStateResponse:
    try:
        # Sector.get_state() ahora devuelve 3 valores (antes 2) --
        # ver el AVISO DE RUPTURA en Sector.get_state.
        cells, atmosphere_cells, bots = sector.get_state()
        return pb.GetStateResponse(
            ok=True, cells=cells, atmosphere_cells=atmosphere_cells, bots=bots
        )
    except Exception as e:
        logger.exception("Error en GetState")
        return pb.GetStateResponse(ok=False, error=str(e))
