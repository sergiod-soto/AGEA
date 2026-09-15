# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/load_state.py
"""
load_state.py — Implementación del RPC LoadState.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

NAME = "LoadState"


async def handle(logica, request, context):
    await logica.load_state(request.snapshot_id)
    return common_pb.Ack(ok=True, error="")
