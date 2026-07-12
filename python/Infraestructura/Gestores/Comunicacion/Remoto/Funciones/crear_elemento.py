# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/crear_elemento.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

COMPONENTE = "LOGICA_MUNDO"
OPERACION = "CrearElemento"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.CrearElementoRequest()
    req.ParseFromString(payload)

    ok, error = await clientes.logica_mundo.crear_elemento(
        pos=(req.pos.x, req.pos.y),
        type_id=req.type_id,
        element=req.element,
    )
    resp = common_pb2.Ack(ok=ok, error=error)
    return resp.SerializeToString()
