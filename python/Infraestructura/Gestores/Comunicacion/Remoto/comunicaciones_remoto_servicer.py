# Infraestructura/Gestores/Comunicacion/Remoto/comunicaciones_remoto_servicer.py


import asyncio
import logging

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    comunicacion_remota_service_pb2 as pb,
    comunicacion_remota_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto import (
    ComunicacionesRemoto,
)

logger = logging.getLogger(__name__)

_TIMEOUT_PING_SEGUNDOS = 3.0

# Nombre del subordinado → nombre del atributo en ClientesRemotos.
_SUBORDINADOS = ("logica_mundo", "gestor_mundo", "gestor_bots")


class ComunicacionesRemotoServicer(pb_grpc.ComunicacionRemotaServiceServicer):

    def __init__(self, logica: ComunicacionesRemoto) -> None:
        self._logica = logica

    async def Heartbeat(self, request, context):
        clientes = self._logica._clientes  # ClientesRemotos ya conectado

        resultados = await asyncio.gather(
            *[
                self._ping(nombre, getattr(clientes, nombre).heartbeat)
                for nombre in _SUBORDINADOS
            ],
            return_exceptions=True,
        )

        # Cualquier resultado que sea una excepción (ver _ping: se
        # lanza tanto por fallo de red como por ok=False del propio
        # subordinado) cuenta como "caído".
        caidos = [
            nombre
            for nombre, resultado in zip(_SUBORDINADOS, resultados)
            if isinstance(resultado, Exception)
        ]

        if caidos:
            logger.error("Heartbeat: subordinados sin respuesta: %s", caidos)
            return common_pb2.Ack(ok=False, error=f"Caídos: {caidos}")
        return common_pb2.Ack(ok=True)

    @staticmethod
    async def _ping(nombre: str, metodo_heartbeat) -> None:
        """
        Llama al heartbeat real del cliente. Se considera "caído" en
        DOS casos, no solo uno:
          1. La llamada lanza excepción (timeout, conexión rechazada,
             proceso muerto).
          2. La llamada responde pero con ok=False — esto ocurre
             cuando el propio subordinado detectó que UNO DE LOS
             SUYOS (un HV, un sector) no responde. Por directiva
             explícita, esto también debe propagar el apagado
             completo, así que se traduce en excepción aquí para que
             Heartbeat() de arriba lo cuente igual que un fallo de red.
        """
        try:
            resp = await asyncio.wait_for(
                metodo_heartbeat(), timeout=_TIMEOUT_PING_SEGUNDOS
            )
        except Exception as exc:
            raise RuntimeError(f"{nombre} no responde: {exc}") from exc

        if not resp.ok:
            raise RuntimeError(f"{nombre} reportó ok=False: {resp.error}")

    async def Ejecutar(self, request, context):
        componente = pb.ComponenteDestino.Name(request.componente)
        ok, error, payload = await self._logica.ejecutar(
            componente, request.operacion, request.payload
        )
        return pb.EjecutarResponse(ok=ok, error=error, payload=payload)

    async def ActualizarFoco(self, request, context):
        """
        Llamado por el master (vía Comunicaciones_Local) para fijar
        la región/filtro que se está mostrando. Traducción directa
        proto -> tuplas nativas; la lógica real vive en
        ComunicacionesRemoto.actualizar_foco (síncrono, solo guarda
        estado, no llama a Logica_Mundo aquí).
        """
        min_pos = (request.min.x, request.min.y)
        max_pos = (request.max.x, request.max.y)
        self._logica.actualizar_foco(
            min_pos, max_pos, list(request.incluir), request.modo
        )
        return common_pb2.Ack(ok=True)

    async def SuscribirseFoco(self, request, context):
        """
        Streaming compartido: cada cliente que llame a este RPC
        (master o espectador) entra en la misma emisión — ver
        FocoBroadcaster.suscribirse(), que es quien realmente vigila
        el tick y reparte. Cuando el cliente se desconecta, gRPC
        cancela esta corrutina; el `finally` de FocoBroadcaster.
        suscribirse() se encarga de quitar la cola correspondiente.
        """
        async for actualizacion in self._logica.suscribirse_foco():
            yield actualizacion
