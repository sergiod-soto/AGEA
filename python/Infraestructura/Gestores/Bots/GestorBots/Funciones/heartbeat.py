# Infraestructura/Gestores/Bots/Gestor_Bots/Funciones/heartbeat.py

from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2 as pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

NAME = "Heartbeat"


async def handle(gestor, request, context):
    caidos = await gestor.hypervisores_caidos()
    hv_statuses = [
        common_pb2.HVStatus(hypervisor_id=hv_id, alive=False, bot_count=0)
        for hv_id in caidos
    ]
    if caidos:
        return pb.GestorBotsHeartbeatResponse(
            ok=False,
            error=f"Hypervisores sin respuesta: {caidos}",
            hv_statuses=hv_statuses,
        )
    return pb.GestorBotsHeartbeatResponse(ok=True, error="")
