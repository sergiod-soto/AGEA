# Infraestructura/Gestores/Mundo/Logica_Mundo/Funciones/get_elementos_globales.py
"""
get_elementos_globales.py — Implementación del RPC GetElementosGlobales.

Sustituye a GestorMundo.GetGlobalState (retirado del proto de
GestorMundoService) — decisión "elementos_globales: B": el estado de
los elementos globales (ciclo día/noche, lunar, clima) siempre vivió
en Logica_Mundo, así que se expone directamente desde aquí en vez de
que Gestor_Mundo tuviera que ir a buscarlo para reenviarlo.
"""

import json

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "GetElementosGlobales"


async def handle(logica, request, context):
    elementos = await logica.get_elementos_globales()
    elementos_pb = [
        pb.ElementoGlobalState(name=nombre, state=json.dumps(estado).encode())
        for nombre, estado in elementos.items()
    ]
    return pb.GetElementosGlobalesResponse(
        ok=True, error="", elementos_globales=elementos_pb
    )
