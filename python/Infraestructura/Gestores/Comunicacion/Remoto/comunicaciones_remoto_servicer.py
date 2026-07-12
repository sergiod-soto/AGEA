# Infraestructura/Gestores/Comunicacion/Remoto/comunicaciones_remoto_servicer.py
"""
comunicaciones_remoto_servicer.py — Servicer gRPC de
ComunicacionRemotaService. Traduce el enum ComponenteDestino a su
nombre en string y delega en ComunicacionesRemoto.ejecutar.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    comunicacion_remota_service_pb2 as pb,
    comunicacion_remota_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto import (
    ComunicacionesRemoto,
)


class ComunicacionesRemotoServicer(pb_grpc.ComunicacionRemotaServiceServicer):

    def __init__(self, logica: ComunicacionesRemoto) -> None:
        self._logica = logica

    async def Ejecutar(self, request, context):
        componente = pb.ComponenteDestino.Name(request.componente)
        ok, error, payload = await self._logica.ejecutar(
            componente, request.operacion, request.payload
        )
        return pb.EjecutarResponse(ok=ok, error=error, payload=payload)
