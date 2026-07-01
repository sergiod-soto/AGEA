# Gestores/Bots/Hypervisor/funciones/set_point_budget.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import common_pb2
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
import logging

logger = logging.getLogger(__name__)
NAME = "SetPointBudget"

def handle(hv: Hypervisor, request, context):
    logger.debug("SetPointBudget: bot=%s puntos=%d", request.bot_id, request.points)
    try:
        hv.set_point_budget(request.bot_id, request.points)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en SetPointBudget")
        return common_pb2.Ack(ok=False, error=str(e))