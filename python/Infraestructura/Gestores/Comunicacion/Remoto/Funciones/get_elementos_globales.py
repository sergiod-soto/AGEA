# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/get_elementos_globales.py
"""
get_elementos_globales.py — Reenvía GetElementosGlobales al lado
LOGICA_MUNDO del puente. Sustituye al antiguo get_global_state.py, que
apuntaba a GESTOR_MUNDO — ver decisión "elementos_globales: B".
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

COMPONENTE = "LOGICA_MUNDO"
OPERACION = "GetElementosGlobales"


async def handle(clientes, payload: bytes) -> bytes:
    resp = await clientes.logica_mundo.get_elementos_globales()
    return resp.SerializeToString()
