# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/spawn_global_event.py
"""
spawn_global_event.py — Implementación del RPC SpawnGlobalEvent.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "SpawnGlobalEvent"


async def handle(logica, request, context):
    event = request.event
    pos = (event.pos.x, event.pos.y) if event.HasField("pos") else None
    ok, error, event_id = await logica.spawn_global_event(
        type_=event.type, pos=pos, payload=event.payload
    )
    return pb.SpawnGlobalEventResponse(ok=ok, error=error, event_id=event_id)
