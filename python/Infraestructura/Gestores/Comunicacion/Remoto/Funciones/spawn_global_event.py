# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/spawn_global_event.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

COMPONENTE = "LOGICA_MUNDO"
OPERACION = "SpawnGlobalEvent"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.SpawnGlobalEventRequest()
    req.ParseFromString(payload)

    event = req.event
    pos = (event.pos.x, event.pos.y) if event.HasField("pos") else None

    # event.event_id se ignora deliberadamente: Logica_Mundo asigna
    # siempre su propio event_id (ver logica_mundo.spawn_global_event).
    ok, error, event_id = await clientes.logica_mundo.spawn_global_event(
        event_id=event.event_id,
        type_=event.type,
        pos=pos,
        payload=event.payload,
    )
    resp = pb.SpawnGlobalEventResponse(ok=ok, error=error, event_id=event_id)
    return resp.SerializeToString()
