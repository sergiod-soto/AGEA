# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/resolver_accion.py
"""
resolver_accion.py — Implementación del RPC ResolverAccion.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

NAME = "ResolverAccion"


async def handle(logica, request, context):
    resultado = await logica.resolver_accion(
        bot_id=request.bot_id,
        action_type=request.action_type,
        payload=request.payload,
    )
    return common_pb.ActionResult(
        ok=resultado.ok,
        payload=resultado.payload,
        error=resultado.error,
        world_tick=resultado.world_tick,
    )
