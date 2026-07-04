# Gestores/Bots/Gestor_Bots/funciones/broadcast_budgets_async.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
import logging

logger = logging.getLogger(__name__)
NAME = "BroadcastBudgetsAsync"


async def handle(gestor: Gestor_Bots, request, context):
    overrides = {entry.bot_id: entry.budget for entry in request.overrides}
    try:
        await gestor.broadcast_budgets_async(request.default_budget, overrides)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en BroadcastBudgetsAsync")
        return common_pb2.Ack(ok=False, error=str(e))
