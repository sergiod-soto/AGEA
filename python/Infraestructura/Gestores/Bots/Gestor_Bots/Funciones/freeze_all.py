# Gestores/Bots/Gestor_Bots/Funciones/freeze_all.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import common_pb2
import logging
logger = logging.getLogger(__name__)
NAME = "FreezeAll"

async def handle(gestor, request, context):
    """
    Pausa todos los HVs. Espera confirmación de cada uno antes de responder.
    """
    try:
        await gestor.freeze_all_async()
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en FreezeAll")
        return common_pb2.Ack(ok=False, error=str(e))