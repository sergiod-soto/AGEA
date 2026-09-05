# Infraestructura/Gestores/Mundo/Logica_Mundo/Funciones/consultar_representacion.py
"""
consultar_representacion.py — Implementación del RPC ConsultarRepresentacion.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "ConsultarRepresentacion"


async def handle(logica, request, context):
    datos = await logica.consultar_representacion(
        min_pos=(request.min.x, request.min.y),
        max_pos=(request.max.x, request.max.y),
        incluir=list(request.incluir),
        modo=request.modo,
    )
    return pb.ConsultarRepresentacionResponse(ok=True, error="", datos=datos)
