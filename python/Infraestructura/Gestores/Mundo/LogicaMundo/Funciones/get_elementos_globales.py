# Infraestructura/Gestores/Mundo/Logica_Mundo/Funciones/get_elementos_globales.py


import json

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

NAME = "GetElementosGlobales"


async def handle(logica, request, context):
    elementos = await logica.get_elementos_globales()
    tick_actual = await logica.get_tick_actual()

    elementos_pb = [
        pb.ElementoGlobalState(name=nombre, state=json.dumps(estado).encode())
        for nombre, estado in elementos.items()
    ]
    return pb.GetElementosGlobalesResponse(
        ok=True,
        error="",
        elementos_globales=elementos_pb,
        tick_actual=tick_actual,
    )
