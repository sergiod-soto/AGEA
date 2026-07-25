# Infraestructura/Gestores/Mundo/Sector/Funciones/shutdown.py
"""
shutdown.py — Implementación del RPC Shutdown.

El proceso se termina DESPUÉS de responder, no antes: si se llamara a
os._exit() directamente aquí, la respuesta gRPC podría no llegar a
enviarse a quien la pidió (main.py o, en remoto, ShutdownCoordinator).
Por eso se agenda el cierre real como una tarea aparte con un pequeño
margen, para dar tiempo a que el propio framework gRPC despache la
respuesta antes de que el proceso desaparezca.
"""

import asyncio
import os

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

NAME = "Shutdown"

_MARGEN_ANTES_DE_SALIR_SEGUNDOS = 0.2


async def handle(sector, request, context):
    async def _salir():
        await asyncio.sleep(_MARGEN_ANTES_DE_SALIR_SEGUNDOS)
        os._exit(0)

    asyncio.create_task(_salir())
    return common_pb2.ShutdownResponse(ok=True, error="")
