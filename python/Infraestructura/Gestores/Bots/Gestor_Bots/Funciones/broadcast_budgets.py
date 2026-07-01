# Gestores/Bots/Gestor_Bots/funciones/broadcast_budgets.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import common_pb2
from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
import logging

logger = logging.getLogger(__name__)
NAME = "BroadcastBudgets"

async def handle(gestor: Gestor_Bots, request, context):
    overrides = {entry.bot_id: entry.budget for entry in request.overrides}
    try:
        gestor.broadcast_budgets(request.default_budget, overrides)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en BroadcastBudgets")
        return common_pb2.Ack(ok=False, error=str(e))