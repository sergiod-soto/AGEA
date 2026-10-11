# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/consultar_representar.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)

COMPONENTE = "LOGICA_MUNDO"
OPERACION = "ConsultarRepresentar"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.ConsultarRepresentarRequest()
    req.ParseFromString(payload)

    datos = await clientes.logica_mundo.consultar_representar(
        min_pos=(req.min.x, req.min.y),
        max_pos=(req.max.x, req.max.y),
        incluir=list(req.incluir) or None,  # [] del proto -> None = "todo"
    )
    resp = pb.ConsultarRepresentarResponse(ok=True, error="", datos=datos)
    return resp.SerializeToString()
