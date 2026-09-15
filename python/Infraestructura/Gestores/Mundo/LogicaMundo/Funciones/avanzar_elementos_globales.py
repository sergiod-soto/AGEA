# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/avanzar_elementos_globales.py
"""
avanzar_elementos_globales.py — Implementación del RPC AvanzarElementosGlobales.
"""

import json

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "AvanzarElementosGlobales"


async def handle(logica, request, context):
    cambios = await logica.avanzar_elementos_globales(request.tick_id)
    return pb.AvanzarElementosGlobalesResponse(
        ok=True, error="", cambios=json.dumps(cambios).encode()
    )