# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/set_step_mode.py

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
)

COMPONENTE = "GESTOR_MUNDO"
OPERACION = "SetStepMode"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.SetStepModeRequest()
    req.ParseFromString(payload)

    ok, error = await clientes.gestor_mundo.set_step_mode(req.activar)
    resp = common_pb2.Ack(ok=ok, error=error)
    return resp.SerializeToString()
