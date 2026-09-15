# Infraestructura/Gestores/Mundo/LogicaMundo/ComandosConsola/obtener_elemento.py

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)
from Infraestructura.Gestores.Mundo.LogicaMundo.logica_mundo import LogicaMundo

TIPO = "ObtenerElemento"


async def handle(logica: LogicaMundo, payload: bytes) -> bytes:
    req = pb.ObtenerElementoRequest()
    req.ParseFromString(payload)

    ok, error, datos = await logica.obtener_elemento(
        element_id=req.element_id,
        tipo_datos=req.tipo_datos or "representacion",
        incluir=list(req.incluir),
    )
    return pb.ObtenerElementoResponse(
        ok=ok, error=error, datos=datos
    ).SerializeToString()
