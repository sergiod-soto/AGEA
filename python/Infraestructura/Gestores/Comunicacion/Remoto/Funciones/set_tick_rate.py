# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/set_tick_rate.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
)

COMPONENTE = "GESTOR_MUNDO"
OPERACION = "SetTickRate"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.SetTickRateRequest()
    req.ParseFromString(payload)

    ok, error = await clientes.gestor_mundo.set_tick_rate(req.ticks_per_second)
    resp = common_pb2.Ack(ok=ok, error=error)
    return resp.SerializeToString()
