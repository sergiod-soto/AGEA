# Gestores/Bots/Gestor_Bots/Funciones/resume_all.py
from Gestores.Transporte.Proto_Generated.Bots import common_pb2
import logging

logger = logging.getLogger(__name__)
NAME = "ResumeAll"


async def handle(gestor, request, context):
    try:
        await gestor.resume_all_async()
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en ResumeAll")
        return common_pb2.Ack(ok=False, error=str(e))
