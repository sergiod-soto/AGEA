# Gestores/Bots/Hypervisor/Funciones/shutdown.py
"""
Migrado a asyncio junto con el resto de Hypervisor: threading.Timer ya
no hace falta (era el equivalente síncrono para retrasar la salida) —
ahora usa el mismo patrón asyncio.create_task que el resto de
componentes (Sector/Gestor_Mundo/Logica_Mundo/Gestor_Bots).
"""

import asyncio
import os

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

NAME = "Shutdown"

_MARGEN_ANTES_DE_SALIR_SEGUNDOS = 0.2


async def handle(hv, request, context):
    async def _salir():
        await asyncio.sleep(_MARGEN_ANTES_DE_SALIR_SEGUNDOS)
        os._exit(0)

    asyncio.create_task(_salir())
    return common_pb2.ShutdownResponse(ok=True, error="")
