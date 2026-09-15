# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/asignar_id.py
"""
asignar_id.py — Implementación del RPC AsignarId.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "AsignarId"


async def handle(logica, request, context):
    nuevo_id = await logica.asignar_id()
    return pb.AsignarIdResponse(id_elemento=nuevo_id)
