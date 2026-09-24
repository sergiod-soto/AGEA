# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/actualizar_celdas_atmosfera.py
"""
actualizar_celdas_atmosfera.py — Implementación del RPC
ActualizarCeldasAtmosfera.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

NAME = "ActualizarCeldasAtmosfera"


async def handle(logica, request, context):
    await logica.actualizar_celdas_atmosfera(list(request.changed_atmosphere_cells))
    return common_pb.Ack(ok=True, error="")
