# Infraestructura/Gestores/Transporte/gestor_mundo_client_sync.py
"""
gestor_mundo_client_sync.py — Cliente SÍNCRONO hacia GestorMundo.

Por qué existe además de gestor_mundo_client.py (asíncrono):
  El Hypervisor es un componente 100% síncrono (grpc.server +
  ThreadPoolExecutor, threading.Lock, sin ningún event loop de asyncio
  corriendo en el proceso). gestor_mundo_client.py expone forward_action
  como `async def` sobre un canal grpc.aio — llamarlo sin `await` desde
  un método síncrono no ejecuta el RPC: crea una coroutine que nadie
  espera, y el reenvío de la acción al Mundo se pierde en silencio.
  Este era exactamente el bug de Hypervisor.forward_to_mundo().

  Gestor_Bots sí es asíncrono y usa correctamente el cliente async (ver
  gestor_bots.py::forward_action_to_mundo, que hace `await`) — ese
  fichero no se toca.

  Este cliente es exclusivo para el Hypervisor, igual que ya tiene su
  propio cliente síncrono para hablar con Gestor_Bots (ver
  gestor_bots_client.py).
"""

import logging

import grpc

from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import ActionResult
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
)

logger = logging.getLogger(__name__)


class GestorMundoClientSync:
    """
    Cliente gRPC síncrono hacia GestorMundo. Solo expone forward_action,
    que es lo único que el Hypervisor necesita. Para el resto de
    operaciones contra el Mundo (usadas por Gestor_Bots, que sí es
    async), seguir usando GestorMundoClient en gestor_mundo_client.py.
    """

    def __init__(self, address: str, timeout: float = 5.0):
        self._address = address
        self._timeout = timeout
        self._channel = grpc.insecure_channel(address)
        self._stub = pb_grpc.GestorMundoServiceStub(self._channel)

    def forward_action(
        self, bot_id: str, action_type: str, payload: bytes = b""
    ) -> ActionResult:
        request = pb.ForwardActionGestorMundoRequest(
            bot_id=bot_id,
            action_type=action_type,
            payload=payload,
        )
        try:
            resp = self._stub.ForwardActionGestorMundo(request, timeout=self._timeout)
            return ActionResult(
                ok=resp.ok,
                payload=resp.payload,
                error=resp.error,
                world_tick=resp.tick_id,
            )
        except grpc.RpcError as exc:
            logger.error("GestorMundoClientSync.forward_action error: %s", exc)
            return ActionResult(ok=False, payload=b"", error=str(exc))

    def close(self) -> None:
        self._channel.close()
