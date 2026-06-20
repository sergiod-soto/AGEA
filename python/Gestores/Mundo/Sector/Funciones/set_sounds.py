from Gestores.Transporte.Proto_Generated.Sectores import sector_service_pb2 as pb
from Gestores.Mundo.Sector.sector import Sector

NAME = "SetSounds"


async def handle(sector: Sector, request, context) -> pb.SetSoundsResponse:
    # TODO: implementar cuando la API de sonido esté definida
    return pb.SetSoundsResponse(ok=True)
