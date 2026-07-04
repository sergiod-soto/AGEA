# Infraestructura/Gestores/Mundo/Gestor_Mundo/Funciones/create_element.py
import grpc
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import (
    GestorMundo,
    SystemState,
)
import logging

logger = logging.getLogger(__name__)

NAME = "CreateElement"


# El RPC CreateElement devuelve common.Ack en el .proto (no un mensaje propio),
# por eso se construye con common_pb2.Ack en vez de un tipo específico de este servicio.
async def handle(gestor: GestorMundo, request, context) -> common_pb2.Ack:
    # Herramienta de dev: solo se permite editar el mundo con la simulación
    # completamente parada, para evitar carreras con el bucle de ticks.
    if gestor._state != SystemState.PAUSED:
        await context.abort(
            grpc.StatusCode.FAILED_PRECONDITION,
            "Operación solo permitida con el mundo en pausa.",
        )
        return common_pb2.Ack(ok=False)
    try:
        key = (request.pos.x, request.pos.y)
        async with gestor._gold_lock:
            if key in gestor._gold_cells:
                return common_pb2.Ack(
                    ok=False, error=f"Ya existe un elemento en ({key[0]},{key[1]})."
                )
            gestor._gold_cells[key] = request.element
            # Reenvía el gold completo a todos los sectores. Es más caro que
            # empujar solo la celda cambiada, pero esta operación solo se usa
            # en dev con el mundo en pausa, así que el coste no importa aquí.
            await gestor._distribute_gold_to_sectors()
        logger.info("[DEV] CreateElement en (%d,%d)", request.pos.x, request.pos.y)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en CreateElement")
        return common_pb2.Ack(ok=False, error=str(e))
