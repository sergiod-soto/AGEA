# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/freeze_all.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2

COMPONENTE = "GESTOR_BOTS"
OPERACION = "FreezeAll"


async def handle(clientes, payload: bytes) -> bytes:
    ok = await clientes.gestor_bots.freeze_all()
    resp = common_pb2.Ack(ok=ok, error="" if ok else "freeze_all falló")
    return resp.SerializeToString()
