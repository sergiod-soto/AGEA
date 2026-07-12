# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/despawn_global_event.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

COMPONENTE = "LOGICA_MUNDO"
OPERACION = "DespawnGlobalEvent"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.DespawnGlobalEventRequest()
    req.ParseFromString(payload)

    ok, error = await clientes.logica_mundo.despawn_global_event(
        req.event_id, req.reason
    )
    resp = common_pb2.Ack(ok=ok, error=error)
    return resp.SerializeToString()
