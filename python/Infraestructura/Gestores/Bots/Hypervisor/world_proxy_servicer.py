"""
world_proxy_servicer.py — Proxy gRPC entre Bots y Mundo.

Cambio respecto a la versión anterior:
  _spend_and_forward() comprueba primero si la acción está delegada.
  Si lo está, el HV la ejecuta localmente y el Mundo nunca se entera.
  Si no lo está, el flujo es idéntico al anterior (forward_to_gestor).

Flujo completo por acción:
  1. Extraer bot-id del header gRPC.
  2. Obtener coste de ACCIONES (fuente de verdad).
  3. try_spend_points → rechazar sin red si no hay puntos.
  4a. Si delegada  → execute_delegated()  (local, sin red)
  4b. Si no        → forward_to_gestor()  (Gestor → Mundo)
  5. Devolver ActionResult al bot.
"""

from __future__ import annotations

import logging

import grpc

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    world_proxy_service_pb2_grpc,
)
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    world_proxy_service_pb2,
)

logger = logging.getLogger(__name__)

_ACTION_COSTS: dict[str, int] | None = None


def _get_action_costs() -> dict[str, int]:
    """
    Lee los costes directamente de api_acciones.py.
    Se llama una vez al primer uso y se cachea en el módulo.
    """
    try:
        from Infraestructura.Gestores.Mundo.api_acciones import ACCIONES

        return {name: entry["coste"] for name, entry in ACCIONES.items()}
    except Exception as exc:
        logger.error("No se pudo cargar ACCIONES para costes: %s", exc)
        return {}


def _costs() -> dict[str, int]:
    global _ACTION_COSTS
    if _ACTION_COSTS is None:
        _ACTION_COSTS = _get_action_costs()
    return _ACTION_COSTS


class WorldProxyServicer(world_proxy_service_pb2_grpc.WorldProxyServiceServicer):
    """
    Servicer gRPC del WorldProxyService (canal Bot → HV).

    Parámetros
    ----------
    hypervisor : Hypervisor
    """

    def __init__(self, hypervisor: Hypervisor):
        self._hv = hypervisor

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_bot_id(context) -> str | None:
        for key, value in context.invocation_metadata():
            if key == "bot-id":
                return value
        return None

    @staticmethod
    def _reject_no_id(context) -> common_pb2.ActionResult:
        context.set_code(grpc.StatusCode.UNAUTHENTICATED)
        context.set_details("Header 'bot-id' ausente.")
        return common_pb2.ActionResult(ok=False, error="bot-id no proporcionado")

    @staticmethod
    def _reject_no_points(bot_id: str, remaining: int) -> common_pb2.ActionResult:
        logger.debug(
            "Bot %s rechazado: puntos insuficientes (restantes: %d).", bot_id, remaining
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
        Núcleo compartido por todos los RPCs de acción.

        1. Identificar bot.
        2. Gastar puntos (local, sin red).
        3a. Acción delegada  → ejecutar en HV, devolver resultado.
        3b. Acción no delegada → reenviar al Gestor → Mundo.
        """
        # 1. Identificar bot
        bot_id = self._extract_bot_id(context)
        if bot_id is None:
            return self._reject_no_id(context)

        # 2. Coste y control de puntos
        cost = _costs().get(action_type, 0)
        ok, remaining = self._hv.try_spend_points(bot_id, cost)
        if not ok:
            return self._reject_no_points(bot_id, remaining)

        # 3a. Acción delegada: el HV la resuelve localmente
        if self._hv.is_delegated(action_type):
            logger.debug(
                "Bot %s — acción '%s' interceptada por HV (local).", bot_id, action_type
            )
            result = self._hv.execute_delegated(bot_id, action_type, payload)
            return common_pb2.ActionResult(
                ok=result.ok,
                payload=result.payload,
                error=result.error,
            )

        # 3b. Acción no delegada: reenviar al Gestor → Mundo
        logger.debug("Bot %s — acción '%s' reenviada al Mundo.", bot_id, action_type)
        try:
            result = self._hv.forward_to_gestor(bot_id, action_type, payload)
        except Exception as exc:
            # Puntos ya descontados — trade-off aceptable (ver comentario original)
            logger.error(
                "forward_to_gestor falló para bot %s acción %s: %s",
                bot_id,
                action_type,
                exc,
            )
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Error de red al reenviar al Gestor.")
            return common_pb2.ActionResult(ok=False, error=str(exc))

        return common_pb2.ActionResult(
            ok=result.ok,
            payload=result.payload,
            error=result.error,
            world_tick=result.world_tick,
        )

    # ------------------------------------------------------------------
    # RPCs
    # ------------------------------------------------------------------

    def Rotar(self, request, context):
        import struct

        payload = struct.pack("<f", request.angle)
        return self._spend_and_forward(context, "rotate", payload)

    def Interact(self, request, context):
        import json

        payload = json.dumps(
            {
                "kind": request.kind,
                "target_id": request.target_id,
                "payload": request.payload.hex(),
            }
        ).encode()
        return self._spend_and_forward(context, "interact", payload)

    def GetStatus(self, request, context):
        """Consulta local — coste 0, nunca sale del HV."""
        bot_id = self._extract_bot_id(context)
        if bot_id is None:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Header 'bot-id' ausente.")
            return world_proxy_service_pb2.BotStatusResponse()

        status = self._hv.get_bot_status(bot_id)
        if status is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Bot {bot_id!r} no encontrado.")
            return world_proxy_service_pb2.BotStatusResponse()

        return world_proxy_service_pb2.BotStatusResponse(
            bot_id=bot_id,
            position=common_pb2.Vector2(x=0.0, y=0.0),
            rotation=0.0,
            health=1.0,
            points_left=status.budget,
            world_tick=0,
            alive=status.alive,
        )
