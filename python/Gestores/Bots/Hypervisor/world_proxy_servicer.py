"""
world_proxy_servicer.py — Implementación gRPC del WorldProxyService.

Es el proxy transparente entre los Bots y el Mundo:
  - Extrae el bot-id del header gRPC en cada llamada.
  - Comprueba el presupuesto de puntos localmente (sin red).
  - Si hay puntos, reenvía la acción al Gestor → Mundo.
  - Devuelve el resultado al bot como si viniera del Mundo.

Canal: Bot → Hypervisor.

Costes de puntos:
    observe   → 1
    move      → 2
    rotate    → 2
    interact  → 3
    get_status → 0  (consulta local, no sube al Gestor)
"""

from __future__ import annotations

import logging

import grpc

from Gestores.Transporte.Proto_Generated import (
    common_pb2,
    world_proxy_service_pb2,
    world_proxy_service_pb2_grpc,
)
from Gestores.Bots.Hypervisor.hypervisor import ACTION_COSTS, Hypervisor

logger = logging.getLogger(__name__)


class WorldProxyServicer(world_proxy_service_pb2_grpc.WorldProxyServiceServicer):
    """
    Servicer gRPC del WorldProxyService (canal Bot → HV).

    Parámetros
    ----------
    hypervisor : Hypervisor
        Instancia ya construida de la lógica pura.
        Se usa para try_spend_points, get_bot_status y forward_to_gestor.
    """

    def __init__(self, hypervisor: Hypervisor):
        self._hv = hypervisor

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_bot_id(context) -> str | None:
        """
        Extrae el bot-id del metadata header gRPC.

        El bot lo manda así:
            metadata = [("bot-id", "mi_bot_001")]
            stub.Observe(request, metadata=metadata)

        Devuelve None si el header no está presente.
        """
        for key, value in context.invocation_metadata():
            if key == "bot-id":
                return value
        return None

    @staticmethod
    def _reject_no_id(context) -> common_pb2.ActionResult:
        """Rechaza la llamada si no viene bot-id en el header."""
        context.set_code(grpc.StatusCode.UNAUTHENTICATED)
        context.set_details("Header 'bot-id' ausente. El bot debe identificarse.")
        return common_pb2.ActionResult(ok=False, error="bot-id no proporcionado")

    @staticmethod
    def _reject_no_points(bot_id: str, remaining: int) -> common_pb2.ActionResult:
        """Rechaza la acción por falta de puntos (sin llamada de red)."""
        logger.debug(
            "Bot %s rechazado por puntos insuficientes (restantes: %d).",
            bot_id, remaining,
        )
        return common_pb2.ActionResult(
            ok=False,
            error=f"Puntos insuficientes (restantes: {remaining})",
        )

    def _spend_and_forward(
        self,
        context,
        action_type: str,
        payload: bytes,
    ) -> common_pb2.ActionResult:
        """
        Núcleo compartido por Observe, Move, Rotate e Interact:
          1. Extrae bot-id del header.
          2. Calcula el coste.
          3. try_spend_points → si falla, rechaza sin red.
          4. forward_to_gestor → resultado del Mundo.
          5. Convierte y devuelve ActionResult protobuf.
        """
        # 1. Identificar al bot
        bot_id = self._extract_bot_id(context)
        if bot_id is None:
            return self._reject_no_id(context)

        # 2. Coste de la acción
        cost = ACTION_COSTS.get(action_type, 0)

        # 3. Control de puntos (local, sin red)
        ok, remaining = self._hv.try_spend_points(bot_id, cost)
        if not ok:
            return self._reject_no_points(bot_id, remaining)

        # 4. Reenviar al Gestor → Mundo
        try:
            result = self._hv.forward_to_gestor(bot_id, action_type, payload)
        except Exception as exc:
            # Si la red falla DESPUÉS de gastar los puntos, los puntos
            # ya se descontaron. Es un trade-off aceptable: preferimos
            # no reembolsar (evita complejidad) y el bot simplemente
            # pierde esa acción. El Mundo no la procesó, así que no hay
            # efecto en el mundo real.
            logger.error(
                "forward_to_gestor falló para bot %s acción %s: %s",
                bot_id, action_type, exc,
            )
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Error de red al reenviar al Gestor.")
            return common_pb2.ActionResult(ok=False, error=str(exc))

        # 5. Convertir resultado a protobuf
        return common_pb2.ActionResult(
            ok=result.ok,
            payload=result.payload,
            error=result.error,
            world_tick=result.world_tick,
        )

    # ------------------------------------------------------------------
    # RPCs
    # ------------------------------------------------------------------

    def Observe(self, request, context):
        """
        El bot observa las entidades cercanas.
        Coste: 1 punto.
        El radio_override (si > 0) se incluye en el payload para que
        el Mundo lo interprete.
        """
        import struct
        # Empaquetamos el radio como 4 bytes float (little-endian)
        # El Mundo lo desempaqueta si lo necesita; si no, lo ignora.
        payload = struct.pack("<f", request.radio_override)

        return self._spend_and_forward(context, "observe", payload)

    def Move(self, request, context):
        """
        El bot se mueve (dx, dy).
        Coste: 2 puntos.
        """
        import struct
        payload = struct.pack("<ff", request.dx, request.dy)
        return self._spend_and_forward(context, "move", payload)

    def Rotate(self, request, context):
        """
        El bot rota al ángulo indicado (radianes).
        Coste: 2 puntos.
        """
        import struct
        payload = struct.pack("<f", request.angle)
        return self._spend_and_forward(context, "rotate", payload)

    def Interact(self, request, context):
        """
        El bot interactúa con una entidad (atacar, recoger, comunicarse).
        Coste: 3 puntos.

        El payload combina kind + target_id + datos extra del request.
        """
        import json
        payload = json.dumps({
            "kind":      request.kind,
            "target_id": request.target_id,
            "payload":   request.payload.hex(),  # bytes → hex string para JSON
        }).encode()

        return self._spend_and_forward(context, "interact", payload)

    def GetStatus(self, request, context):
        """
        Consulta el estado del bot (puntos, posición, salud).
        Coste: 0 puntos. Respuesta local — no sube al Gestor.

        La posición y salud las devuelve el Hypervisor con lo que sabe;
        si el Mundo actualiza esos datos vía ActionResult, el Hypervisor
        puede cachearlos. Por ahora devolvemos lo que tenemos localmente.
        """
        bot_id = self._extract_bot_id(context)
        if bot_id is None:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Header 'bot-id' ausente.")
            return world_proxy_service_pb2.BotStatusResponse()

        status = self._hv.get_bot_status(bot_id)
        if status is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Bot {bot_id!r} no encontrado en este Hypervisor.")
            return world_proxy_service_pb2.BotStatusResponse()

        return world_proxy_service_pb2.BotStatusResponse(
            bot_id=bot_id,
            # Posición y rotación: el HV no las cachea todavía;
            # el Mundo las conoce. Se puede extender BotRecord más adelante.
            position=common_pb2.Vector2(x=0.0, y=0.0),
            rotation=0.0,
            health=1.0,
            points_left=status.budget,
            world_tick=0,
            alive=status.alive,
        )
