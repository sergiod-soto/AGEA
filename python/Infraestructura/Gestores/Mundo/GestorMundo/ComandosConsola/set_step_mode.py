# Infraestructura/Gestores/Mundo/Gestor_Mundo/ComandosConsola/set_step_mode.py

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import GestorMundo

TIPO = "SetStepMode"


async def handle(gestor: GestorMundo, payload: bytes) -> bytes:
    """
    payload trae un SetStepModeRequest serializado. Se devuelve un
    common_pb2.Ack serializado, igual que si fuera un RPC normal —
    solo cambia CÓMO llega la petición, no la forma de la respuesta.
    """
    req = pb.SetStepModeRequest()
    req.ParseFromString(payload)
    ok, error = gestor.activar_modo_paso(req.activar)
    return common_pb2.Ack(ok=ok, error=error).SerializeToString()
