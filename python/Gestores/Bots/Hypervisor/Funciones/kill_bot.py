# Gestores/Bots/Hypervisor/funciones/kill_bot.py
from Gestores.Transporte.Proto_Generated.Bots import common_pb2
from Gestores.Bots.Hypervisor.hypervisor import Hypervisor
import logging

logger = logging.getLogger(__name__)
NAME = "KillBot"

def handle(hv: Hypervisor, request, context):
    logger.info("KillBot: bot_id=%s", request.bot_id)
    try:
        hv.kill_bot(request.bot_id)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en KillBot")
        return common_pb2.Ack(ok=False, error=str(e))