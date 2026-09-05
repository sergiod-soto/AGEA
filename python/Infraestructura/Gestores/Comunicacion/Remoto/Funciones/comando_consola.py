# Infraestructura/Gestores/Comunicacion/Remoto/Funciones/comando_consola.py

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
)

COMPONENTE = "GESTOR_MUNDO"
OPERACION = "ComandoConsola"


async def handle(clientes, payload: bytes) -> bytes:
    req = pb.ComandoConsolaRequest()
    req.ParseFromString(payload)

    ok, error, resultado = await clientes.gestor_mundo.ejecutar_comando_consola(
        req.tipo, req.payload
    )
    resp = pb.ComandoConsolaResponse(ok=ok, error=error, payload=resultado)
    return resp.SerializeToString()
