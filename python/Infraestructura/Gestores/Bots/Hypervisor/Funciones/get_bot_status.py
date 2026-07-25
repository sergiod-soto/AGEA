# Gestores/Bots/Hypervisor/funciones/get_bot_status.py
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
import grpc
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

logger = logging.getLogger(__name__)
NAME = "GetBotStatus"

async def handle(hv, request, context):
    try:
        status = await hv.get_bot_status(request.bot_id)
    except Exception as e:
        logger.exception("Error en GetBotStatus")
        return common_pb2.BotStatus()
    if status is None:
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details(f"Bot {request.bot_id!r} no encontrado")
        return common_pb2.BotStatus()
    return common_pb2.BotStatus(
        bot_id=status.bot_id, alive=status.alive, budget=status.budget,
    )