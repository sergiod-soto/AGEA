# Gestores/Mundo/Gestor_Mundo/funciones/delete_element.py
import grpc

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo, SystemState
import logging

logger = logging.getLogger(__name__)
NAME = "DeleteElement"

async def handle(gestor: GestorMundo, request, context) -> pb.DeleteElementResponse:
    if gestor._state != SystemState.PAUSED:
        await context.abort(grpc.StatusCode.FAILED_PRECONDITION,
                            "Operación solo permitida con el mundo en pausa.")
        return pb.DeleteElementResponse(ok=False)
    try:
        key = (request.pos.x, request.pos.y)
        async with gestor._gold_lock:
            if key not in gestor._gold_cells:
                return pb.DeleteElementResponse(
                    ok=False, error=f"No hay elemento en ({key[0]},{key[1]})."
                )
            gestor._gold_cells.pop(key)
            await gestor._distribuir_celda_modificada(key, b"")
        logger.info("[DEV] DeleteElement en (%d,%d)", request.pos.x, request.pos.y)
        return pb.DeleteElementResponse(ok=True)
    except Exception as e:
        logger.exception("Error en DeleteElement")
        return pb.DeleteElementResponse(ok=False, error=str(e))