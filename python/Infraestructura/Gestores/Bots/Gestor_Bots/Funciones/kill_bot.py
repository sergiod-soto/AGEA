# Gestores/Bots/Gestor_Bots/funciones/kill_bot.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import common_pb2
from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
import logging

logger = logging.getLogger(__name__)
NAME = "KillBot"


async def handle(gestor: Gestor_Bots, request, context):
    logger.info("KillBot: bot_id=%s", request.bot_id)
    try:
        await gestor.kill_bot(request.bot_id)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en KillBot")
        return common_pb2.Ack(ok=False, error=str(e))
