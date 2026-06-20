"""
bot_client.py — Cliente gRPC del WorldProxyService.

Carpeta: Hypervisores/Transporte/bot_client.py

El bot lo instancia con la dirección proxy recibida al hacer spawn.
El bot_id se inyecta automáticamente en el header de cada llamada.

Para añadir soporte a una acción nueva:
  1. Añadir la acción en core/acciones.py  ← obligatorio
  2. Añadir un método de conveniencia aquí ← opcional pero recomendado

El método act() genérico siempre funciona para cualquier acción,
aunque no tenga método de conveniencia.

Uso básico
----------
    from Hypervisores.Transporte.bot_client import BotClient

    client = BotClient(bot_id="bot_001", proxy_address="localhost:50053")

    # Método genérico (siempre disponible)
    result = client.act("observe", payload=...)

    # Métodos de conveniencia
    hits   = client.observe(center_angle=0.0, fov=1.57, num_rays=5)
    result = client.move(dx=1, dy=0)
    result = client.reproduce()
    status = client.get_status()

    client.close()
"""

from __future__ import annotations

import json
import logging
import struct
from dataclasses import dataclass
from typing import Optional

import grpc

from Gestores.Mundo.action_result import ActionResult
from Gestores.Transporte.Proto_Generated import (
    common_pb2,
    world_proxy_service_pb2,
    world_proxy_service_pb2_grpc,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tipos de retorno
# ---------------------------------------------------------------------------




@dataclass
class RayHit:
    hit: bool
    type: int  # common_pb2.EntityType
    distance: int  # casillas


@dataclass
class ObserveResult:
    rays: list[RayHit]
    ok: bool = True
    error: str = ""

    def __bool__(self):
        return self.ok


@dataclass
class BotStatus:
    bot_id: str
    x: int
    y: int
    rotation: float
    health: float
    points_left: int
    world_tick: int
    alive: bool


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------


class BotClient:
    """
    Cliente gRPC del WorldProxyService.

    Parámetros
    ----------
    bot_id : str
        ID único del bot. Se inyecta en cada llamada como header gRPC.
    proxy_address : str
        "host:puerto" del WorldProxyService del Hypervisor asignado.
    timeout : float
        Timeout por defecto en segundos (default 10 s).
    """

    def __init__(
        self,
        bot_id: str,
        proxy_address: str,
        timeout: float = 10.0,
    ):
        self.bot_id = bot_id
        self._proxy_address = proxy_address
        self._timeout = timeout
        self._metadata = [("bot-id", bot_id)]

        self._channel = grpc.insecure_channel(
            proxy_address,
            options=[
                ("grpc.max_receive_message_length", 256 * 1024 * 1024),
                ("grpc.max_send_message_length", 256 * 1024 * 1024),
                ("grpc.keepalive_time_ms", 20_000),
                ("grpc.keepalive_timeout_ms", 10_000),
            ],
        )
        self._stub = world_proxy_service_pb2_grpc.WorldProxyServiceStub(self._channel)
        logger.info("BotClient %r → %s", bot_id, proxy_address)

    def close(self):
        self._channel.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _t(self, timeout: Optional[float]) -> float:
        return timeout if timeout is not None else self._timeout

    def _handle_rpc_error(self, method: str, exc: grpc.RpcError) -> ActionResult:
        code = exc.code()
        details = exc.details() or str(exc)
        if code in (grpc.StatusCode.UNAUTHENTICATED, grpc.StatusCode.PERMISSION_DENIED):
            logger.error("%s: error de autenticación — %s", method, details)
        elif "Puntos insuficientes" in details:
            logger.debug("%s: sin puntos — %s", method, details)
        else:
            logger.error("%s falló: %s — %s", method, code, details)
        return ActionResult(ok=False, error=details)

    # ------------------------------------------------------------------
    # Método genérico — siempre disponible para cualquier acción
    # ------------------------------------------------------------------

    def act(
        self,
        action_name: str,
        payload: bytes = b"",
        timeout: float | None = None,
    ) -> ActionResult:
        """
        Envía cualquier acción al Mundo a través del Hypervisor.

        action_name debe coincidir con una clave de core/acciones.py.
        payload es el contenido específico de la acción (bytes opacos).

        Usar los métodos de conveniencia (observe, move...) cuando existan;
        usar este método directamente para acciones sin método propio.
        """
        request = world_proxy_service_pb2.ActRequest(
            action_name=action_name,
            payload=payload,
        )
        try:
            pb = self._stub.Act(
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
            return self._handle_rpc_error(f"Act({action_name})", exc)

    # ------------------------------------------------------------------
    # Métodos de conveniencia — uno por acción conocida
    # ------------------------------------------------------------------

    def observe(
        self,
        center_angle: float,
        fov: float,
        num_rays: int,
        timeout: float | None = None,
    ) -> ObserveResult:
        """
        Raycast en abanico.
        Coste: ver core/acciones.py → "observe".

        center_angle : ángulo central del abanico (radianes)
        fov          : apertura total del abanico (radianes)
        num_rays     : número de rayos

        Devuelve ObserveResult con la lista de RayHit deserializada.
        """
        payload = struct.pack("<ffi", center_angle, fov, num_rays)
        result = self.act("observe", payload, timeout)

        if not result.ok:
            return ObserveResult(rays=[], ok=False, error=result.error)

        # Deserializar payload → ObserveResult protobuf
        try:
            pb = common_pb2.ObserveResult()
            pb.ParseFromString(result.payload)
            rays = [
                RayHit(hit=r.hit, type=r.type, distance=r.distance) for r in pb.rays
            ]
            return ObserveResult(rays=rays, ok=True)
        except Exception as exc:
            logger.error("Error deserializando ObserveResult: %s", exc)
            return ObserveResult(rays=[], ok=False, error=str(exc))

    def move(
        self,
        dx: int,
        dy: int,
        timeout: float | None = None,
    ) -> ActionResult:
        """
        Mover el bot dx casillas en X y dy en Y.
        Coste: ver core/acciones.py → "move".
        """
        payload = struct.pack("<ii", dx, dy)
        return self.act("move", payload, timeout)

    def rotate(
        self,
        angle: float,
        timeout: float | None = None,
    ) -> ActionResult:
        """
        Rotar el bot al ángulo indicado (radianes, absoluto).
        Coste: ver core/acciones.py → "rotate".
        """
        payload = struct.pack("<f", angle)
        return self.act("rotate", payload, timeout)

    def interact(
        self,
        kind: str,
        target_id: str,
        data: bytes = b"",
        timeout: float | None = None,
    ) -> ActionResult:
        """
        Interacción genérica con una entidad.
        Coste: ver core/acciones.py → "interact".

        kind      : "attack" | "pickup" | "communicate"
        target_id : ID de la entidad objetivo
        data      : bytes extra (p.ej. mensaje en communicate)
        """
        payload = json.dumps(
            {
                "kind": kind,
                "target_id": target_id,
                "data": data.hex(),
            }
        ).encode()
        return self.act("interact", payload, timeout)

    def broadcast(
        self,
        message: bytes,
        radius: int,
        timeout: float | None = None,
    ) -> ActionResult:
        """
        Emitir un mensaje a todos los bots en radio X casillas.
        Coste: ver core/acciones.py → "broadcast".
        El Mundo limita el tamaño del mensaje por ciclo.
        """
        payload = struct.pack("<i", radius) + message
        return self.act("broadcast", payload, timeout)

    def reproduce(
        self,
        timeout: float | None = None,
    ) -> ActionResult:
        """
        Solicitar reproducción asexual al Mundo.
        Coste: ver core/acciones.py → "reproduce".
        El Mundo decide si aprueba la solicitud según sus condiciones internas.
        El payload del resultado indicará el bot_id del hijo si se aprueba.
        """
        return self.act("reproduce", b"", timeout)

    # ------------------------------------------------------------------
    # Estado propio (0 puntos, consulta local al Hypervisor)
    # ------------------------------------------------------------------

    def get_status(self, timeout: float | None = None) -> Optional[BotStatus]:
        """
        Consulta el estado del bot (puntos restantes, vivo/muerto).
        Coste: 0 puntos. No sube al Gestor ni al Mundo.

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
                return None
            self._handle_rpc_error("GetStatus", exc)
            return None
