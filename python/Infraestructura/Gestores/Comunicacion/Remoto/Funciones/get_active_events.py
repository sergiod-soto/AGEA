# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/get_active_events.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

COMPONENTE = "LOGICA_MUNDO"
OPERACION = "GetActiveEvents"


async def handle(clientes, payload: bytes) -> bytes:
    # LogicaMundoClient.get_active_events() ya devuelve una lista de
    # GlobalEvent (proto) sin interpretarla — se reenvía tal cual.
    eventos = await clientes.logica_mundo.get_active_events()
    resp = pb.GetActiveEventsResponse(ok=True, error="", events=eventos)
    return resp.SerializeToString()
