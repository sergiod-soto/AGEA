# Gestores/Bots/Hypervisor/funciones/list_bots.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import common_pb2
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
import logging

logger = logging.getLogger(__name__)
NAME = "ListBots"

def handle(hv: Hypervisor, request, context):
    try:
        bot_list = hv.list_bots()
        return common_pb2.BotList(bots=[
            common_pb2.BotStats(
                bot_id=s.bot_id, hypervisor_id=s.hypervisor_id,
                points_left=s.points_left, fitness=0.0, tick=0,
            )
            for s in bot_list.bots
        ])
    except Exception as e:
        logger.exception("Error en ListBots")
        return common_pb2.BotList()