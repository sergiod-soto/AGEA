# Gestores/Bots/Gestor_Bots/funciones/list_hypervisors.py
from Gestores.Transporte.Proto_Generated.Bots import common_pb2
from Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
import logging

logger = logging.getLogger(__name__)
NAME = "ListHypervisors"


async def handle(gestor: Gestor_Bots, request, context):
    try:
        hv_list = await gestor.list_hypervisors()
        return common_pb2.HypervisorList(
            hypervisors=[
                common_pb2.HypervisorInfo(
                    hypervisor_id=hv.hypervisor_id,
                    address=hv.address,
                    port=hv.port,
                    proxy_port=hv.proxy_port,
                    capacity=hv.capacity,
                    current_load=hv.current_load,
                    online=hv.online,
                )
                for hv in hv_list.hypervisors
            ]
        )
    except Exception as e:
        logger.exception("Error en ListHypervisors")
        return common_pb2.HypervisorList()
