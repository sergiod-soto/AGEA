# Infraestructura/Gestores/Mundo/Gestor_Mundo/Funciones/modify_element.py
import grpc
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo, SystemState
import logging

logger = logging.getLogger(__name__)

NAME = "ModifyElement"


async def handle(gestor: GestorMundo, request, context) -> common_pb2.Ack:
    if gestor._state != SystemState.PAUSED:
        await context.abort(grpc.StatusCode.FAILED_PRECONDITION,
                            "Operación solo permitida con el mundo en pausa.")
        return common_pb2.Ack(ok=False)
    try:
        key = (request.pos.x, request.pos.y)
        async with gestor._gold_lock:
            if key not in gestor._gold_cells:
                return common_pb2.Ack(
                    ok=False, error=f"No hay elemento en ({key[0]},{key[1]})."
                )
            gestor._gold_cells[key] = request.patch
            await gestor._distribute_gold_to_sectors()
        logger.info("[DEV] ModifyElement en (%d,%d)", request.pos.x, request.pos.y)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en ModifyElement")
        return common_pb2.Ack(ok=False, error=str(e))