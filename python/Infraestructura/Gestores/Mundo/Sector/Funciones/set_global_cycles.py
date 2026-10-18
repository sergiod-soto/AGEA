# Infraestructura/Gestores/Mundo/Sector/Funciones/set_global_cycles.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as pb,
)
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
import logging

logger = logging.getLogger(__name__)
NAME = "SetGlobalCycles"


async def handle(sector: Sector, request, context) -> pb.SetGlobalCyclesResponse:
    try:
        sector.set_ciclos_globales(
            tick_id=request.tick_id,
            progreso_solar=request.progreso_solar,
            progreso_lunar=request.progreso_lunar,
            progreso_anual=request.progreso_anual,
        )
        return pb.SetGlobalCyclesResponse(ok=True)
    except Exception as e:
        logger.exception("Error en SetGlobalCycles")
        return pb.SetGlobalCyclesResponse(ok=False, error=str(e))
