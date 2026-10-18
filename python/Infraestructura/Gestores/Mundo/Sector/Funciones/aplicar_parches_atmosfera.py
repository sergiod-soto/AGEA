# Infraestructura/Gestores/Mundo/Sector/Funciones/aplicar_parches_atmosfera.py

"""RPC AplicarParchesAtmosfera (fase 0): aplica al Sector los cambios de terreno
de atmósfera que Logica (gold) ha parcheado desde el tick anterior."""

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as pb,
)

NAME = "AplicarParchesAtmosfera"


async def handle(sector, request, context):
    try:
        sector.aplicar_parches_atmosfera(request.tick_id, list(request.cells))
        return pb.AplicarParchesAtmosferaResponse(ok=True)
    except Exception as exc:
        # El Gestor lo trata como fatal (fase 0).
        return pb.AplicarParchesAtmosferaResponse(ok=False, error=str(exc))
