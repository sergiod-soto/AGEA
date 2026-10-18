# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/tomar_parches_atmosfera.py

"""RPC TomarParchesAtmosfera: entrega al Gestor los parches de terreno de
atmósfera pendientes y los vacía (ver LogicaMundo.tomar_parches_atmosfera)."""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)
import logging

logger = logging.getLogger(__name__)


NAME = "TomarParchesAtmosfera"


async def handle(logica, request, context):
    try:
        cells = await logica.tomar_parches_atmosfera()
        return pb.TomarParchesAtmosferaResponse(ok=True, cells=cells)
    except Exception as exc:
        # El Gestor lo trata como fatal: los parches ya se habían vaciado.
        logger.exception("Error en TomarParchesAtmosfera")
        return pb.TomarParchesAtmosferaResponse(
            ok=False, error=f"{type(exc).__name__}: {exc}"
        )
