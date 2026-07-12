# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/eliminar_elemento.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

COMPONENTE = "LOGICA_MUNDO"
OPERACION = "EliminarElemento"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.EliminarElementoRequest()
    req.ParseFromString(payload)

    ok, error = await clientes.logica_mundo.eliminar_elemento(
        pos=(req.pos.x, req.pos.y),
        element_id=req.element_id,
    )
    resp = common_pb2.Ack(ok=ok, error=error)
    return resp.SerializeToString()
