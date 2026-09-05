# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/advance_tick.py

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
)

COMPONENTE = "GESTOR_MUNDO"
OPERACION = "AdvanceTick"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.AdvanceTickRequest()
    req.ParseFromString(payload)

    ok, error = await clientes.gestor_mundo.advance_tick()
    resp = common_pb2.Ack(ok=ok, error=error)
    return resp.SerializeToString()
