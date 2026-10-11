# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/consultar_representar.py
"""
consultar_representar.py — Implementación del RPC ConsultarRepresentar.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "ConsultarRepresentar"


async def handle(logica, request, context):
    datos = await logica.consultar_representar(
        min_pos=(request.min.x, request.min.y),
        max_pos=(request.max.x, request.max.y),
        incluir=list(request.incluir),
    )
    return pb.ConsultarRepresentarResponse(ok=True, error="", datos=datos)
