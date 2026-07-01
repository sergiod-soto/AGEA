# Gestores/Mundo/Sector/funciones/set_sector_mode.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import sector_service_pb2 as pb
from Infraestructura.Gestores.Mundo.Sector.sector import Sector, SectorMode

NAME = "SetSectorMode"

async def handle(sector: Sector, request, context) -> pb.SetSectorModeResponse:
    try:
        mode = SectorMode(request.mode)
        sector.set_mode(mode)
        return pb.SetSectorModeResponse(ok=True)
    except ValueError as e:
        return pb.SetSectorModeResponse(ok=False, error=f"Modo desconocido: {e}")
    except Exception as e:
        return pb.SetSectorModeResponse(ok=False, error=str(e))