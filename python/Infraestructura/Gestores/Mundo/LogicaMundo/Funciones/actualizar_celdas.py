# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/actualizar_celdas.py
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

logger = logging.getLogger(__name__)
NAME = "ActualizarCeldas"


async def handle(logica, request, context):
    """Aplica el resultado de un tick de Sector (celdas cambiadas)."""
    try:
        await logica.actualizar_celdas(list(request.changed_cells))
        return pb.ActualizarCeldasResponse(ok=True)
    except Exception as e:
        logger.exception("Error en ActualizarCeldas")
        return pb.ActualizarCeldasResponse(ok=False, error=str(e))
