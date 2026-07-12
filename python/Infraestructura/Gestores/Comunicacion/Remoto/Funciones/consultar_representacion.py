# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/consultar_representacion.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

COMPONENTE = "LOGICA_MUNDO"
OPERACION = "ConsultarRepresentacion"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.ConsultarRepresentacionRequest()
    req.ParseFromString(payload)

    datos = await clientes.logica_mundo.consultar_representacion(
        min_pos=(req.min.x, req.min.y),
        max_pos=(req.max.x, req.max.y),
        incluir=list(req.incluir),
        modo=req.modo,
    )
    resp = pb.ConsultarRepresentacionResponse(ok=True, error="", datos=datos)
    return resp.SerializeToString()
