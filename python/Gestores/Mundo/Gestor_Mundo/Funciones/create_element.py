# Gestores/Mundo/Gestor_Mundo/funciones/create_element.py
import grpc

from Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo, SystemState
import logging

logger = logging.getLogger(__name__)
NAME = "CreateElement"

async def handle(gestor: GestorMundo, request, context) -> pb.CreateElementResponse:
    if gestor._state != SystemState.PAUSED:
        await context.abort(grpc.StatusCode.FAILED_PRECONDITION,
                            "Operación solo permitida con el mundo en pausa.")
        return pb.CreateElementResponse(ok=False)
    try:
        key = (request.pos.x, request.pos.y)
        async with gestor._gold_lock:
            if key in gestor._gold_cells:
                return pb.CreateElementResponse(
                    ok=False, error=f"Ya existe un elemento en ({key[0]},{key[1]})."
                )
            gestor._gold_cells[key] = request.element
            await gestor._distribuir_celda_modificada(key, request.element)
        logger.info("[DEV] CreateElement en (%d,%d)", request.pos.x, request.pos.y)
        return pb.CreateElementResponse(ok=True)
    except Exception as e:
        logger.exception("Error en CreateElement")
        return pb.CreateElementResponse(ok=False, error=str(e))