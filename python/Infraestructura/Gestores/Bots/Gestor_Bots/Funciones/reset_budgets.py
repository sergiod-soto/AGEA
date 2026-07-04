# Gestores/Bots/Gestor_Bots/Funciones/reset_budgets.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
import logging

logger = logging.getLogger(__name__)
NAME = "ResetBudgets"


async def handle(gestor, request, context):
    """
    Llamado por el Mundo cada tick.
    Hace broadcast del budget por defecto a todos los HVs.
    ResetBudgetsRequest está vacío — el budget por defecto
    viene de la config del gestor.
    """
    try:
        await gestor.broadcast_budgets_async(
            default_budget=gestor.bots_por_hypervisor,
            overrides=None,
        )
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en ResetBudgets")
        return common_pb2.Ack(ok=False, error=str(e))
