# Gestores/Bots/Hypervisor/funciones/reset_budgets.py
from Gestores.Transporte.Proto_Generated.Bots import common_pb2
from Gestores.Bots.Hypervisor.hypervisor import Hypervisor
import logging

logger = logging.getLogger(__name__)
NAME = "ResetBudgets"

def handle(hv: Hypervisor, request, context):
    overrides = {entry.bot_id: entry.budget for entry in request.overrides}
    new_budgets = {
        bot_id: overrides.get(bot_id, request.default_budget)
        for bot_id in request.bot_ids
    }
    logger.info(
        "ResetBudgets: %d bot(s), default=%d, overrides=%d",
        len(request.bot_ids), request.default_budget, len(overrides),
    )
    try:
        hv.reset_budgets(list(request.bot_ids), new_budgets)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en ResetBudgets")
        return common_pb2.Ack(ok=False, error=str(e))