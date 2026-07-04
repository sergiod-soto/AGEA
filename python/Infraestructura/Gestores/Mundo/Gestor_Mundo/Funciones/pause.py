from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
import logging

logger = logging.getLogger(__name__)
NAME = "Pause"


async def handle(gestor: GestorMundo, request, context) -> common_pb2.Ack:
    try:
        await gestor.freeze()
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en Pause")
        return common_pb2.Ack(ok=False, error=str(e))
