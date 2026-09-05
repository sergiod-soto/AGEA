# Gestores/Bots/Gestor_Bots/funciones/update_hypervisor_load.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Bots.GestorBots.gestor_bots import Gestor_Bots
import logging

logger = logging.getLogger(__name__)
NAME = "UpdateHypervisorLoad"


async def handle(gestor: Gestor_Bots, request, context):
    try:
        await gestor.update_hypervisor_load(request.hypervisor_id, request.current_load)
        return common_pb2.Ack(ok=True)
    except Exception as e:
        logger.exception("Error en UpdateHypervisorLoad")
        return common_pb2.Ack(ok=False, error=str(e))
