# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/modificar_elemento.py
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

COMPONENTE = "LOGICA_MUNDO"
OPERACION = "ModificarElemento"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.ModificarElementoRequest()
    req.ParseFromString(payload)

    # patch viaja como bytes opacos — Logica_Mundo es quien lo
    # deserializa a dict (ver Logica_Mundo/Funciones/modificar_elemento.py).
    ok, error = await clientes.logica_mundo.modificar_elemento(
        pos=(req.pos.x, req.pos.y),
        type_id=req.type_id,
        patch=req.patch,
    )
    resp = common_pb2.Ack(ok=ok, error=error)
    return resp.SerializeToString()
