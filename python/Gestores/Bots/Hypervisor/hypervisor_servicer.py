"""
hypervisor_servicer.py — Implementación gRPC del HypervisorService.

Traduce mensajes protobuf ↔ tipos Python y delega toda la lógica
en la instancia de Hypervisor inyectada en el constructor.

Canal: Gestor → Hypervisor.
No confundir con world_proxy_servicer.py (canal Bot → Hypervisor).

No contiene lógica de negocio; solo conversión y gestión de errores gRPC.
"""

from __future__ import annotations

import logging

import grpc

from Gestores.Transporte.Proto_Generated import (
    common_pb2,
    hypervisor_service_pb2,
    hypervisor_service_pb2_grpc,
)
from Gestores.Bots.Hypervisor.hypervisor import Hypervisor

logger = logging.getLogger(__name__)


class HypervisorServicer(hypervisor_service_pb2_grpc.HypervisorServiceServicer):
    """
    Servicer gRPC del HypervisorService (canal Gestor → HV).

    Parámetros
    ----------
    hypervisor : Hypervisor
        Instancia ya construida de la lógica pura.
    """

    def __init__(self, hypervisor: Hypervisor):
        self._hv = hypervisor

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ack(ok: bool = True, error: str = "") -> common_pb2.Ack:
        return common_pb2.Ack(ok=ok, error=error)

    @staticmethod
    def _stats_to_pb(stats) -> common_pb2.BotStats:
        return common_pb2.BotStats(
            bot_id=stats.bot_id,
            hypervisor_id=stats.hypervisor_id,
            points_left=stats.points_left,
            # fitness y tick los conoce el Mundo/Gestor, no el HV
            fitness=0.0,
            tick=0,
        )

    # ------------------------------------------------------------------
    # RPCs — ciclo de vida de bots
    # ------------------------------------------------------------------

    def SpawnBot(self, request, context):
        """
        El Gestor ordena registrar un bot en este HV.
        Traduce BotConfig protobuf → dict Python y delega en Hypervisor.
        """
        cfg = request.config
        bot_config = {
            "bot_id":    cfg.bot_id,
            "codigo_gz": cfg.codigo_gz,
            "budget":    cfg.budget,
            "metadata":  dict(cfg.metadata),
        }

        logger.info("SpawnBot recibido del Gestor: bot_id=%s", cfg.bot_id)

        try:
            info = self._hv.spawn_bot(bot_config)
        except Exception as exc:
            logger.exception("Error en SpawnBot")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return common_pb2.BotInfo(ok=False, error=str(exc))

        return common_pb2.BotInfo(
            bot_id=info.bot_id,
            hypervisor_id=info.hypervisor_id,
            ok=info.ok,
            error=info.error,
        )

    def KillBot(self, request, context):
        logger.info("KillBot recibido del Gestor: bot_id=%s", request.bot_id)
        try:
            self._hv.kill_bot(request.bot_id)
        except Exception as exc:
            logger.exception("Error en KillBot")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return self._ack(False, str(exc))
        return self._ack()

    def GetBotStats(self, request, context):
        try:
            stats = self._hv.get_bot_stats(request.bot_id)
        except Exception as exc:
            logger.exception("Error en GetBotStats")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return common_pb2.BotStats()

        if stats is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Bot {request.bot_id!r} no encontrado en este HV")
            return common_pb2.BotStats()

        return self._stats_to_pb(stats)

    def ListBots(self, request, context):
        try:
            bot_list = self._hv.list_bots()
        except Exception as exc:
            logger.exception("Error en ListBots")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return common_pb2.BotList()

        return common_pb2.BotList(
            bots=[self._stats_to_pb(s) for s in bot_list.bots]
        )

    # ------------------------------------------------------------------
    # RPCs — control de presupuesto
    # ------------------------------------------------------------------

    def ResetBudgets(self, request, context):
        """
        El Gestor resetea los presupuestos al inicio de cada ciclo.

        Construimos el dict de overrides desde la lista de BudgetEntry
        y delegamos en Hypervisor.reset_budgets.
        """
        overrides = {entry.bot_id: entry.budget for entry in request.overrides}

        # Construimos el mapa completo: cada bot recibe su presupuesto correcto
        new_budgets: dict[str, int] = {}
        for bot_id in request.bot_ids:
            new_budgets[bot_id] = overrides.get(bot_id, request.default_budget)

        logger.info(
            "ResetBudgets: %d bot(s), default=%d, overrides=%d",
            len(request.bot_ids), request.default_budget, len(overrides),
        )

        try:
            self._hv.reset_budgets(list(request.bot_ids), new_budgets)
        except Exception as exc:
            logger.exception("Error en ResetBudgets")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return self._ack(False, str(exc))

        return self._ack()

    def SetPointBudget(self, request, context):
        logger.debug(
            "SetPointBudget: bot=%s puntos=%d", request.bot_id, request.points
        )
        try:
            self._hv.set_point_budget(request.bot_id, request.points)
        except Exception as exc:
            logger.exception("Error en SetPointBudget")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return self._ack(False, str(exc))
        return self._ack()

    # ------------------------------------------------------------------
    # RPCs — consultas de estado
    # ------------------------------------------------------------------

    def GetBotStatus(self, request, context):
        try:
            status = self._hv.get_bot_status(request.bot_id)
        except Exception as exc:
            logger.exception("Error en GetBotStatus")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return common_pb2.BotStatus()

        if status is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Bot {request.bot_id!r} no encontrado en este HV")
            return common_pb2.BotStatus()

        return common_pb2.BotStatus(
            bot_id=status.bot_id,
            alive=status.alive,
            budget=status.budget,
        )
