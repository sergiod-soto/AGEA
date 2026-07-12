# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/resume.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

COMPONENTE = "GESTOR_MUNDO"
OPERACION = "Resume"


async def handle(clientes, payload: bytes) -> bytes:
    ok, error = await clientes.gestor_mundo.resume()
    resp = common_pb2.Ack(ok=ok, error=error)
    return resp.SerializeToString()
