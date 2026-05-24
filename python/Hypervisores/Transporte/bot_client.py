"""
bot_client.py — Cliente gRPC del WorldProxyService.

Carpeta: Hypervisores/Transporte/bot_client.py

Usado por los Bots para interactuar con el Mundo.
El bot no sabe que hay un Hypervisor en medio: solo conoce
la dirección proxy que recibió al hacer spawn.

El bot_id se inyecta automáticamente en el header gRPC de
cada llamada. El Hypervisor lo extrae para controlar puntos.

Uso básico
----------
    from Hypervisores.Transporte.bot_client import BotClient

    # proxy_address viene de BotInfo.proxy_address tras el spawn
    client = BotClient(bot_id="bot_001", proxy_address="localhost:50053")

    # Observar entidades cercanas
    result = client.observe()
    if result.ok:
        print(result.payload)   # bytes con entidades serializadas

    # Moverse
    result = client.move(dx=1.0, dy=0.0)

    # Rotar
    result = client.rotate(angle=1.57)   # ~90 grados

    # Interactuar
    result = client.interact_attack(target_id="bot_002")
    result = client.interact_pickup(target_id="item_007")
    result = client.interact_communicate(target_id="bot_003", message=b"hola")

    # Consultar estado propio (0 puntos)
    status = client.get_status()
    print(status.points_left)

    # Cerrar al terminar
    client.close()

    # O con context manager
    with BotClient("bot_001", "localhost:50053") as client:
        result = client.observe()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import grpc

from Hypervisores.Transporte.Proto_Generated import (
    common_pb2,
    world_proxy_service_pb2,
    world_proxy_service_pb2_grpc,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tipos de retorno
# ---------------------------------------------------------------------------

@dataclass
class ActionResult:
    """Resultado de una acción enviada al Mundo."""
    ok:         bool
    payload:    bytes = b""
    error:      str   = ""
    world_tick: int   = 0

    def __bool__(self):
        return self.ok


@dataclass
class BotStatus:
    """Estado propio del bot devuelto por get_status()."""
    bot_id:     str
    x:          float
    y:          float
    rotation:   float
    health:     float
    points_left: int
    world_tick: int
    alive:      bool


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------

class BotClient:
    """
    Cliente gRPC del WorldProxyService.

    El bot lo instancia una vez al arrancar con la dirección proxy
    que recibió del Gestor al hacer spawn.

    Parámetros
    ----------
    bot_id : str
        Identificador único del bot. Se inyecta en cada llamada gRPC
        como header ("bot-id", bot_id).
    proxy_address : str
        "host:puerto" del WorldProxyService del Hypervisor asignado.
        Ejemplo: "192.168.1.10:50053"
    timeout : float
        Timeout por defecto para cada RPC en segundos (default 10 s).
    """

    def __init__(
        self,
        bot_id: str,
        proxy_address: str,
        timeout: float = 10.0,
    ):
        self.bot_id        = bot_id
        self._proxy_address = proxy_address
        self._timeout       = timeout

        # El metadata se construye una sola vez y se reutiliza en cada llamada
        self._metadata = [("bot-id", bot_id)]

        self._channel = grpc.insecure_channel(
            proxy_address,
            options=[
                ("grpc.max_receive_message_length", 256 * 1024 * 1024),
                ("grpc.max_send_message_length",    256 * 1024 * 1024),
                ("grpc.keepalive_time_ms",          20_000),
                ("grpc.keepalive_timeout_ms",       10_000),
            ],
        )
        self._stub = world_proxy_service_pb2_grpc.WorldProxyServiceStub(self._channel)

        logger.info(
            "BotClient %r conectado a proxy %s", bot_id, proxy_address
        )

    def close(self):
        """Cierra el canal. Llamar al terminar el bot."""
        self._channel.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _t(self, timeout: Optional[float]) -> float:
        return timeout if timeout is not None else self._timeout

    def _handle_error(self, method: str, exc: grpc.RpcError) -> ActionResult:
        code    = exc.code()
        details = exc.details()

        if code == grpc.StatusCode.PERMISSION_DENIED or \
           code == grpc.StatusCode.UNAUTHENTICATED:
            logger.error("%s: error de autenticación — %s", method, details)

        elif code == grpc.StatusCode.RESOURCE_EXHAUSTED or \
             "Puntos insuficientes" in (details or ""):
            # El Hypervisor rechazó por falta de puntos; no es un error grave
            logger.debug("%s: sin puntos — %s", method, details)

        else:
            logger.error("%s falló: código=%s detalle=%s", method, code, details)

        return ActionResult(ok=False, error=details or str(exc))

    # ------------------------------------------------------------------
    # Acciones principales
    # ------------------------------------------------------------------

    def observe(
        self,
        radio_override: float = 0.0,
        timeout: float | None = None,
    ) -> ActionResult:
        """
        Observa las entidades cercanas al bot.
        Coste: 1 punto.

        radio_override: radio de visión personalizado (0.0 = usar el del Mundo).
        El payload del resultado contiene las entidades serializadas.
        """
        request = world_proxy_service_pb2.ObserveRequest(
            radio_override=radio_override
        )
        try:
            pb = self._stub.Observe(
                request,
                metadata=self._metadata,
                timeout=self._t(timeout),
            )
            return ActionResult(
                ok=pb.ok,
                payload=pb.payload,
                error=pb.error,
                world_tick=pb.world_tick,
            )
        except grpc.RpcError as exc:
            return self._handle_error("Observe", exc)

    def move(
        self,
        dx: float,
        dy: float,
        timeout: float | None = None,
    ) -> ActionResult:
        """
        Mueve el bot (dx, dy) en coordenadas del mundo.
        Coste: 2 puntos.
        """
        request = world_proxy_service_pb2.MoveRequest(dx=dx, dy=dy)
        try:
            pb = self._stub.Move(
                request,
                metadata=self._metadata,
                timeout=self._t(timeout),
            )
            return ActionResult(ok=pb.ok, payload=pb.payload,
                                error=pb.error, world_tick=pb.world_tick)
        except grpc.RpcError as exc:
            return self._handle_error("Move", exc)

    def rotate(
        self,
        angle: float,
        timeout: float | None = None,
    ) -> ActionResult:
        """
        Rota el bot al ángulo indicado (radianes, absoluto).
        Coste: 2 puntos.
        """
        request = world_proxy_service_pb2.RotateRequest(angle=angle)
        try:
            pb = self._stub.Rotate(
                request,
                metadata=self._metadata,
                timeout=self._t(timeout),
            )
            return ActionResult(ok=pb.ok, payload=pb.payload,
                                error=pb.error, world_tick=pb.world_tick)
        except grpc.RpcError as exc:
            return self._handle_error("Rotate", exc)

    # ------------------------------------------------------------------
    # Interacciones (wrappers sobre Interact para mayor legibilidad)
    # ------------------------------------------------------------------

    def interact_attack(
        self,
        target_id: str,
        timeout: float | None = None,
    ) -> ActionResult:
        """Ataca a la entidad target_id. Coste: 3 puntos."""
        return self._interact(
            kind=world_proxy_service_pb2.INTERACT_ATTACK,
            target_id=target_id,
            payload=b"",
            timeout=timeout,
        )

    def interact_pickup(
        self,
        target_id: str,
        timeout: float | None = None,
    ) -> ActionResult:
        """Recoge el item target_id. Coste: 3 puntos."""
        return self._interact(
            kind=world_proxy_service_pb2.INTERACT_PICKUP,
            target_id=target_id,
            payload=b"",
            timeout=timeout,
        )

    def interact_communicate(
        self,
        target_id: str,
        message: bytes,
        timeout: float | None = None,
    ) -> ActionResult:
        """
        Envía un mensaje (bytes) a target_id.
        Coste: 3 puntos.
        El contenido de message es libre — el bot y el receptor
        acuerdan el formato fuera del proto.
        """
        return self._interact(
            kind=world_proxy_service_pb2.INTERACT_COMMUNICATE,
            target_id=target_id,
            payload=message,
            timeout=timeout,
        )

    def _interact(
        self,
        kind: int,
        target_id: str,
        payload: bytes,
        timeout: float | None,
    ) -> ActionResult:
        """Método interno común para todas las interacciones."""
        request = world_proxy_service_pb2.InteractRequest(
            kind=kind,
            target_id=target_id,
            payload=payload,
        )
        try:
            pb = self._stub.Interact(
                request,
                metadata=self._metadata,
                timeout=self._t(timeout),
            )
            return ActionResult(ok=pb.ok, payload=pb.payload,
                                error=pb.error, world_tick=pb.world_tick)
        except grpc.RpcError as exc:
            return self._handle_error("Interact", exc)

    # ------------------------------------------------------------------
    # Estado propio (0 puntos)
    # ------------------------------------------------------------------

    def get_status(self, timeout: float | None = None) -> Optional[BotStatus]:
        """
        Consulta el estado actual del bot (puntos, posición, salud).
        Coste: 0 puntos. No sube al Gestor.

        Devuelve None si hay error de red o el bot no existe en el HV.
        """
        request = world_proxy_service_pb2.GetStatusRequest()
        try:
            pb = self._stub.GetStatus(
                request,
                metadata=self._metadata,
                timeout=self._t(timeout),
            )
            return BotStatus(
                bot_id=pb.bot_id,
                x=pb.position.x,
                y=pb.position.y,
                rotation=pb.rotation,
                health=pb.health,
                points_left=pb.points_left,
                world_tick=pb.world_tick,
                alive=pb.alive,
            )
        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.NOT_FOUND:
                logger.warning(
                    "get_status: bot %r no encontrado en el HV.", self.bot_id
                )
                return None
            self._handle_error("GetStatus", exc)
            return None
