# Gestores/Bots/Hypervisor/Funciones/get_bot_stats.py
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
import grpc
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

logger = logging.getLogger(__name__)
NAME = "GetBotStats"


def handle(hv: Hypervisor, request, context):
    try:
        stats = hv.get_bot_stats(request.bot_id)
    except Exception as e:
        logger.exception("Error en GetBotStats")
        return common_pb2.BotStats()
    if stats is None:
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details(f"Bot {request.bot_id!r} no encontrado")
        return common_pb2.BotStats()
    return common_pb2.BotStats(
        bot_id=stats.bot_id,
        hypervisor_id=stats.hypervisor_id,
        points_left=stats.points_left,
        fitness=0.0,
        tick=0,
    )
