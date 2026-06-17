# Gestores/Bots/Gestor_Bots/funciones/register_hypervisor.py
from Gestores.Transporte.Proto_Generated.Bots import gestor_bots_service_pb2 as pb
from Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
import logging

logger = logging.getLogger(__name__)
NAME = "RegisterHypervisor"

def handle(gestor: Gestor_Bots, request, context):
    logger.info(
        "RegisterHypervisor: %s en %s:%d (proxy:%d, cap:%d)",
        request.hypervisor_id, request.address, request.port,
        request.proxy_port, request.capacity,
    )
    try:
        gestor.register_hypervisor(
            hypervisor_id=request.hypervisor_id,
            address=request.address,
            port=request.port,
            proxy_port=request.proxy_port,
            capacity=request.capacity,
        )
        delegated = gestor.get_delegated_action_names()
        return pb.RegisterHVAck(ok=True, delegated_actions=delegated)
    except Exception as e:
        logger.exception("Error en RegisterHypervisor")
        return pb.RegisterHVAck(ok=False, error=str(e))