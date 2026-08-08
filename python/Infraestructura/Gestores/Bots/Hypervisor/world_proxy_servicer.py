# Infraestructura/Gestores/Bots/Hypervisor/world_proxy_servicer.py
"""
world_proxy_servicer.py — Proxy gRPC entre Bots y Mundo.

Flujo completo por acción (vía Act):
  1. Extraer bot-id del header gRPC.
  2. Obtener coste de ACCIONES (fuente de verdad).
  3. try_spend_points → rechazar sin red si no hay puntos.
  4. forward_to_gestor()  (Gestor → Mundo)
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

logger = logging.getLogger(__name__)

_ACTION_COSTS: dict[str, int] | None = None


def _get_action_costs() -> dict[str, int]:
    """
    Lee los costes directamente de api_acciones.py.
    Se llama una vez al primer uso y se cachea en el módulo.
    """
    try:
        from Infraestructura.Gestores.Mundo.Logica_Mundo.api_acciones import ACCIONES

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
    def _reject_no_points(bot_id: int, remaining: int) -> common_pb2.ActionResult:
        logger.debug(
            "Bot %s rechazado: puntos insuficientes (restantes: %d).", bot_id, remaining
        )
        return common_pb2.ActionResult(
            ok=False,
            error=f"Puntos insuficientes (restantes: {remaining})",
        )

    async def _spend_and_forward(
        self,
        context,
        action_type: str,
        payload: bytes,
    ) -> common_pb2.ActionResult:
        """
        Núcleo compartido por Act() para cualquier action_name.

        1. Identificar bot.
        2. Gastar puntos (local, sin red).
        3. Reenviar al Gestor → Mundo (única vía: ver ELIMINADO en la
           cabecera del fichero sobre por qué ya no hay rama delegada).
        """
        # 1. Identificar bot
        bot_id = self._extract_bot_id(context)
        if bot_id is None:
            return self._reject_no_id(context)

        # 2. Coste y control de puntos
        cost = _costs().get(action_type, 0)
        ok, remaining = await self._hv.try_spend_points(bot_id, cost)
        if not ok:
            return self._reject_no_points(bot_id, remaining)

        # 3. Reenviar al Gestor → Mundo
        logger.debug("Bot %s — acción '%s' reenviada al Mundo.", bot_id, action_type)
        try:
            result = await self._hv.forward_to_gestor(bot_id, action_type, payload)
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

    async def Act(self, request, context):
        """
        Único punto de entrada de acciones del bot — el único RPC que
        declara world_proxy_service.proto. request.action_name debe
        coincidir con una clave registrada en api_acciones.ACCIONES;
        request.payload es su contenido específico, en bytes opacos
        para este servicer (cada acción interpreta su propio payload).
        """
        return await self._spend_and_forward(
            context, request.action_name, request.payload
        )
