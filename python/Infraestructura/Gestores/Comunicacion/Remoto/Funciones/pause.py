# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/pause.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

COMPONENTE = "GESTOR_MUNDO"
OPERACION = "Pause"


async def handle(clientes, payload: bytes) -> bytes:
    ok, error = await clientes.gestor_mundo.pause()
    resp = common_pb2.Ack(ok=ok, error=error)
    return resp.SerializeToString()
