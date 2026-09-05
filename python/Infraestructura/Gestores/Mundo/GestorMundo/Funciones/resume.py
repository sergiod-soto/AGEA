from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import GestorMundo
import logging

logger = logging.getLogger(__name__)
NAME = "Resume"


async def handle(gestor: GestorMundo, request, context) -> common_pb2.Ack:
    try:
        await gestor.resume()
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en Resume")
        return common_pb2.Ack(ok=False, error=str(e))
