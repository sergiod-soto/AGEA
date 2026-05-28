"""
gestor_servicer.py — Implementación gRPC del GestorService.

Traduce mensajes protobuf ↔ tipos Python y delega toda la lógica
en la instancia de Gestor inyectada en el constructor.

No contiene lógica de negocio; solo conversión y gestión de errores gRPC.
"""

from __future__ import annotations

import logging

import grpc

from Hypervisores.Transporte.Proto_Generated import (
    common_pb2,
    gestor_service_pb2,
    gestor_service_pb2_grpc,
)
from Hypervisores.Gestor.gestor import Gestor

logger = logging.getLogger(__name__)


class GestorServicer(gestor_service_pb2_grpc.GestorServiceServicer):
    """
    Servicer gRPC del Gestor.

    Parámetros
    ----------
    gestor : Gestor
        Instancia ya construida de la lógica pura.
    hypervisor_client_factory : callable
        Función (address: str, port: int) → cliente HypervisorClient.
        Se llama al registrar un nuevo Hypervisor para guardar el canal de vuelta.
    """

    def __init__(self, gestor: Gestor, hypervisor_client_factory=None):
        self._gestor = gestor
        self._hv_client_factory = hypervisor_client_factory

    # ------------------------------------------------------------------
    # Helpers de conversión
    # ------------------------------------------------------------------

    @staticmethod
    def _bot_info_to_pb(info) -> common_pb2.BotInfo:
        return common_pb2.BotInfo(
            bot_id=info.bot_id,
            hypervisor_id=info.hypervisor_id,
            proxy_address=info.proxy_address,
            ok=info.ok,
            error=info.error,
        )

    @staticmethod
    def _ack(ok: bool = True, error: str = "") -> common_pb2.Ack:
        return common_pb2.Ack(ok=ok, error=error)

    @staticmethod
    def _bot_stats_to_pb(stats) -> common_pb2.BotStats:
        return common_pb2.BotStats(
            bot_id=stats.bot_id,
            hypervisor_id=stats.hypervisor_id,
            fitness=stats.fitness,
            tick=stats.tick,
        )

    @staticmethod
    def _hv_info_to_pb(hv) -> common_pb2.HypervisorInfo:
        return common_pb2.HypervisorInfo(
            hypervisor_id=hv.hypervisor_id,
            address=hv.address,
            port=hv.port,
            proxy_port=hv.proxy_port,
            capacity=hv.capacity,
            current_load=hv.current_load,
            online=hv.online,
        )

    # ------------------------------------------------------------------
    # RPCs — ciclo de vida de bots (llamados por el Mundo)
    # ------------------------------------------------------------------

    def SpawnBot(self, request, context):
        """
        El Mundo pide crear un bot. Traduce BotConfig protobuf → dict Python,
        delega en Gestor.spawn_bot y devuelve BotInfo.
        """
        cfg = request.config
        bot_config = {
            "bot_id": cfg.bot_id,
            "codigo_gz": cfg.codigo_gz,
            "budget": cfg.budget,
            "metadata": dict(cfg.metadata),
        }

        logger.info("SpawnBot solicitado: bot_id=%s", cfg.bot_id)

        try:
            info = self._gestor.spawn_bot(bot_config)
        except Exception as exc:
            logger.exception("Error en SpawnBot")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return common_pb2.BotInfo(ok=False, error=str(exc))

        return self._bot_info_to_pb(info)

    def KillBot(self, request, context):
        logger.info("KillBot: bot_id=%s", request.bot_id)
        try:
            self._gestor.kill_bot(request.bot_id)
        except Exception as exc:
            logger.exception("Error en KillBot")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return self._ack(False, str(exc))
        return self._ack()

    def UpdateFitness(self, request, context):
        try:
            self._gestor.update_fitness(request.bot_id, request.fitness, request.tick)
        except Exception as exc:
            logger.exception("Error en UpdateFitness")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return self._ack(False, str(exc))
        return self._ack()

    def BuildFitnessReport(self, request, context):
        try:
            report = self._gestor.build_fitness_report()
        except Exception as exc:
            logger.exception("Error en BuildFitnessReport")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return common_pb2.FitnessReport()

        entries = [
            common_pb2.FitnessEntry(
                bot_id=e.bot_id,
                fitness=e.fitness,
                tick=e.tick,
            )
            for e in report.entries
        ]
        return common_pb2.FitnessReport(entries=entries)

    def BroadcastBudgets(self, request, context):
        """
        El Mundo ordena resetear los presupuestos de todos los bots.
        Los overrides individuales llegan como lista de BudgetEntry.
        """
        overrides = {entry.bot_id: entry.budget for entry in request.overrides}
        try:
            self._gestor.broadcast_budgets(request.default_budget, overrides)
        except Exception as exc:
            logger.exception("Error en BroadcastBudgets")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return self._ack(False, str(exc))
        return self._ack()

    # ------------------------------------------------------------------
    # RPCs — registro y control de Hypervisores
    # ------------------------------------------------------------------

    def RegisterHypervisor(self, request, context):
        """
        Un Hypervisor arranca y se registra aquí.
        Además de guardar los metadatos, creamos el cliente de vuelta
        (Gestor → Hypervisor) usando el factory inyectado.
        """
        logger.info(
            "RegisterHypervisor: %s en %s:%d (proxy:%d, cap:%d)",
            request.hypervisor_id,
            request.address,
            request.port,
            request.proxy_port,
            request.capacity,
        )
        try:
            self._gestor.register_hypervisor(
                hypervisor_id=request.hypervisor_id,
                address=request.address,
                port=request.port,
                proxy_port=request.proxy_port,
                capacity=request.capacity,
            )

            # Creamos el canal de vuelta Gestor → Hypervisor
            if self._hv_client_factory is not None:
                client = self._hv_client_factory(request.address, request.port)
                self._gestor.set_hypervisor_client(request.hypervisor_id, client)
            else:
                logger.warning(
                    "Sin hypervisor_client_factory; el Gestor no podrá llamar al HV %s",
                    request.hypervisor_id,
                )
        except Exception as exc:
            logger.exception("Error en RegisterHypervisor")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return self._ack(False, str(exc))

        return self._ack()

    def UpdateHypervisorLoad(self, request, context):
        try:
            self._gestor.update_hypervisor_load(
                request.hypervisor_id, request.current_load
            )
        except Exception as exc:
            logger.exception("Error en UpdateHypervisorLoad")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return self._ack(False, str(exc))
        return self._ack()

    def ListHypervisors(self, request, context):
        try:
            hv_list = self._gestor.list_hypervisors()
        except Exception as exc:
            logger.exception("Error en ListHypervisors")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return common_pb2.HypervisorList()

        return common_pb2.HypervisorList(
            hypervisors=[self._hv_info_to_pb(hv) for hv in hv_list.hypervisors]
        )

    # ------------------------------------------------------------------
    # RPCs — reenvío de acciones al Mundo
    # ------------------------------------------------------------------

    def ForwardAction(self, request, context):
        """
        El Hypervisor ha validado los puntos del bot y sube la acción aquí.
        El Gestor la reenvía al Mundo y nos devuelve el ActionResult.
        """
        logger.debug(
            "ForwardAction: bot=%s hv=%s tipo=%s",
            request.bot_id,
            request.hypervisor_id,
            request.action_type,
        )
        try:
            result = self._gestor.forward_action_to_mundo(
                bot_id=request.bot_id,
                hypervisor_id=request.hypervisor_id,
                action_type=request.action_type,
                payload=request.payload,
            )
        except Exception as exc:
            logger.exception("Error en ForwardAction")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return common_pb2.ActionResult(ok=False, error=str(exc))

        return common_pb2.ActionResult(
            ok=result.ok,
            payload=result.payload,
            error=result.error,
        )
