# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/obtener_progreso_ciclos.py
"""
obtener_progreso_ciclos.py — Implementación del RPC ObtenerProgresoCiclos.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "ObtenerProgresoCiclos"


async def handle(logica, request, context):
    (
        progreso_solar,
        progreso_lunar,
        progreso_anual,
    ) = await logica.obtener_progreso_ciclos()
    return pb.ObtenerProgresoCiclosResponse(
        ok=True,
        error="",
        progreso_solar=progreso_solar,
        progreso_lunar=progreso_lunar,
        progreso_anual=progreso_anual,
    )
