# Infraestructura/Gestores/Mundo/LogicaMundo/Funciones/shutdown.py


import asyncio
import os

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

NAME = "Shutdown"

_MARGEN_ANTES_DE_SALIR_SEGUNDOS = 0.2


async def handle(logica, request, context):
    async def _salir():
        await asyncio.sleep(_MARGEN_ANTES_DE_SALIR_SEGUNDOS)
        os._exit(0)

    asyncio.create_task(_salir())
    return common_pb2.ShutdownResponse(ok=True, error="")
