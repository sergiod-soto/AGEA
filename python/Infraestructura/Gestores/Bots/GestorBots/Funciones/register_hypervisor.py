# Gestores/Bots/Gestor_Bots/funciones/register_hypervisor.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2 as pb,
)
from Infraestructura.Gestores.Bots.GestorBots.gestor_bots import Gestor_Bots
import logging

logger = logging.getLogger(__name__)

NAME = "RegisterHypervisor"


async def handle(gestor, request, context):

    logger.info(
        "RegisterHypervisor: %s en %s:%d (proxy:%d, cap:%d)",
        request.hypervisor_id,
        request.address,
        request.port,
        request.proxy_port,
        request.capacity,
    )
    try:
        await gestor.register_hypervisor(
            hypervisor_id=request.hypervisor_id,
            address=request.address,
            port=request.port,
            proxy_port=request.proxy_port,
            capacity=request.capacity,
        )
        return pb.RegisterHVAck(ok=True, delegated_actions=[])
    except Exception as e:
        logger.exception("Error en RegisterHypervisor")
        return pb.RegisterHVAck(ok=False, error=str(e))
