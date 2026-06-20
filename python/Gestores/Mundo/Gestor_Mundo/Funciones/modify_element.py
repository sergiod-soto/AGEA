# Gestores/Mundo/Gestor_Mundo/funciones/modify_element.py
import grpc

from Gestores.Transporte.Proto_Generated.Sectores import gestor_mundo_service_pb2 as pb
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo, SystemState
import logging

logger = logging.getLogger(__name__)
NAME = "ModifyElement"

async def handle(gestor: GestorMundo, request, context) -> pb.ModifyElementResponse:
    if gestor._state != SystemState.PAUSED:
        await context.abort(grpc.StatusCode.FAILED_PRECONDITION,
                            "Operación solo permitida con el mundo en pausa.")
        return pb.ModifyElementResponse(ok=False)
    try:
        key = (request.pos.x, request.pos.y)
        async with gestor._gold_lock:
            if key not in gestor._gold_cells:
                return pb.ModifyElementResponse(
                    ok=False, error=f"No hay elemento en ({key[0]},{key[1]})."
                )
            gestor._gold_cells[key] = request.patch
            await gestor._distribuir_celda_modificada(key, request.patch)
        logger.info("[DEV] ModifyElement en (%d,%d)", request.pos.x, request.pos.y)
        return pb.ModifyElementResponse(ok=True)
    except Exception as e:
        logger.exception("Error en ModifyElement")
        return pb.ModifyElementResponse(ok=False, error=str(e))