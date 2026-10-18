# Infraestructura/Gestores/Mundo/Sector/Funciones/aplicar_parches_atmosfera.py

"""RPC AplicarParchesAtmosfera (fase 0): aplica al Sector los cambios de terreno
de atmósfera que Logica (gold) ha parcheado desde el tick anterior."""

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2 as pb,
)
import logging

logger = logging.getLogger(__name__)

NAME = "AplicarParchesAtmosfera"


async def handle(sector, request, context):
    try:
        sector.aplicar_parches_atmosfera(request.tick_id, list(request.cells))
        return pb.AplicarParchesAtmosferaResponse(ok=True)
    except Exception as exc:
        # El Gestor lo trata como fatal: los parches ya se habían vaciado.
        logger.exception("Error en TomarParchesAtmosfera")
        return pb.TomarParchesAtmosferaResponse(
            ok=False, error=f"{type(exc).__name__}: {exc}"
        )
