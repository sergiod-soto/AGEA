# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/list_hypervisors.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

COMPONENTE = "GESTOR_BOTS"
OPERACION = "ListHypervisors"


async def handle(clientes, payload: bytes) -> bytes:
    """
    Devuelve common.HypervisorList — mismo mensaje que ya usa
    GestorBotsService.ListHypervisors, sin inventar una forma nueva.
    """
    lista = await clientes.gestor_bots.list_hypervisors()
    resp = common_pb2.HypervisorList(
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
            for hv in lista.hypervisors
        ]
    )
    return resp.SerializeToString()
