# Infraestructura/Gestores/Mundo/Logica_Mundo/Funciones/get_active_events.py
"""
get_active_events.py — Implementación del RPC GetActiveEvents.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "GetActiveEvents"


async def handle(logica, request, context):
    eventos = await logica.get_active_events()
    eventos_pb = [
        pb.GlobalEvent(
            event_id=ev.event_id,
            type=ev.type,
            pos=common_pb.Position(x=ev.pos[0], y=ev.pos[1]) if ev.pos else common_pb.Position(),
            payload=ev.payload,
        )
        for ev in eventos
    ]
    return pb.GetActiveEventsResponse(ok=True, error="", events=eventos_pb)