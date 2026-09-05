# Infraestructura/Gestores/Mundo/Logica_Mundo/Funciones/actualizar_celdas.py
"""
actualizar_celdas.py — Implementación del RPC ActualizarCeldas.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb

NAME = "ActualizarCeldas"


async def handle(logica, request, context):
    await logica.actualizar_celdas(list(request.changed_cells))
    return common_pb.Ack(ok=True, error="")
