# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/avanzar_tick.py
"""
avanzar_tick — Implementación del RPC AvanzarTick.

Avanza el tiempo del mundo un tick (tick actual + reloj). Es independiente
de los elementos globales: ver LogicaMundo.avanzar_tick.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

NAME = "AvanzarTick"


async def handle(logica, request, context):

    await logica.avanzar_tick(request.tick_id)
    return common_pb.Ack(ok=True, error="")
