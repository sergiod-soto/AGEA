# Infraestructura/Gestores/Gestores/Comunicacion/Remoto/Funciones/resume_all.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

COMPONENTE = "GESTOR_BOTS"
OPERACION = "ResumeAll"


async def handle(clientes, payload: bytes) -> bytes:
    ok = await clientes.gestor_bots.resume_all()
    resp = common_pb2.Ack(ok=ok, error="" if ok else "resume_all falló")
    return resp.SerializeToString()
