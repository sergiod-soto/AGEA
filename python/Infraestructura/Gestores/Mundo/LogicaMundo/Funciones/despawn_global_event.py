# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/despawn_global_event.py
"""
despawn_global_event.py — Implementación del RPC DespawnGlobalEvent.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

NAME = "DespawnGlobalEvent"


async def handle(logica, request, context):
    ok, error = await logica.despawn_global_event(request.event_id, request.reason)
    return common_pb.Ack(ok=ok, error=error)