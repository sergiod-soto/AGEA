# Infraestructura/Gestores/Transporte/hypervisor_client.py
"""
hypervisor_client.py — Cliente async gRPC del HypervisorService.
Usado exclusivamente por el Gestor para dar órdenes a un Hypervisor concreto.
"""

from __future__ import annotations

import logging
from typing import Optional

import grpc
import grpc.aio

from Infraestructura.Gestores.tipos_comunes import (
    BotInfo,
    BotList,
    BotStats,
    BotStatusHV,
)
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    hypervisor_service_pb2_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    hypervisor_service_pb2,
)

logger = logging.getLogger(__name__)

_GRPC_OPTIONS = [
    ("grpc.max_receive_message_length", 256 * 1024 * 1024),
    ("grpc.max_send_message_length", 256 * 1024 * 1024),
    ("grpc.keepalive_time_ms", 20_000),
    ("grpc.keepalive_timeout_ms", 10_000),
]


class HypervisorClient:
    """
    Cliente async gRPC del HypervisorService.
    Una instancia por cada HV registrado en el Gestor.
    """

    def __init__(self, address: str, port: int, timeout: float = 10.0):
        self._address = address
        self._port = port
        self._timeout = timeout
        self._target = f"{address}:{port}"

        self._channel = grpc.aio.insecure_channel(self._target, options=_GRPC_OPTIONS)
        self._stub = hypervisor_service_pb2_grpc.HypervisorServiceStub(self._channel)
        logger.info("HypervisorClient conectado a %s", self._target)

    async def close(self) -> None:
        await self._channel.close()

    def _t(self, timeout: Optional[float]) -> float:
        return timeout if timeout is not None else self._timeout

    def _handle_error(self, method: str, exc: grpc.aio.AioRpcError) -> None:
        logger.error(
            "%s → %s falló: código=%s detalle=%s",
            self._target,
            method,
            exc.code(),
            exc.details(),
        )

    # ------------------------------------------------------------------
    # Ciclo de vida de bots
    # ------------------------------------------------------------------

    async def spawn_bot(
        self, bot_config: dict, timeout: float | None = None
    ) -> BotInfo:
        cfg = common_pb2.BotConfig(
            bot_id=bot_config.get("bot_id", ""),
            codigo_gz=bot_config.get("codigo_gz", b""),
            budget=int(bot_config.get("budget", 100)),
            metadata=bot_config.get("metadata", {}),
        )
        request = hypervisor_service_pb2.SpawnBotRequest(config=cfg)
        try:
            pb = await self._stub.SpawnBot(request, timeout=self._t(timeout))
            return BotInfo(
                bot_id=pb.bot_id,
                hypervisor_id=pb.hypervisor_id,
                proxy_address="",
                ok=pb.ok,
                error=pb.error,
            )
        except grpc.aio.AioRpcError as exc:
            self._handle_error("SpawnBot", exc)
            return BotInfo(
                bot_id=bot_config.get("bot_id", ""),
                hypervisor_id="",
                proxy_address="",
                ok=False,
                error=str(exc),
            )

    async def kill_bot(self, bot_id: str, timeout: float | None = None) -> bool:
        request = hypervisor_service_pb2.BotIdRequest(bot_id=bot_id)
        try:
            pb = await self._stub.KillBot(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.aio.AioRpcError as exc:
            self._handle_error("KillBot", exc)
            return False

    async def get_bot_stats(
        self, bot_id: str, timeout: float | None = None
    ) -> Optional[BotStats]:
        request = hypervisor_service_pb2.BotIdRequest(bot_id=bot_id)
        try:
            pb = await self._stub.GetBotStats(request, timeout=self._t(timeout))
            return BotStats(
                bot_id=pb.bot_id,
                hypervisor_id=pb.hypervisor_id,
                points_left=pb.points_left,
                alive=True,
            )
        except grpc.aio.AioRpcError as exc:
            if exc.code() == grpc.StatusCode.NOT_FOUND:
                return None
            self._handle_error("GetBotStats", exc)
            return None

    async def get_bot_status(
        self, bot_id: str, timeout: float | None = None
    ) -> Optional[BotStatusHV]:
        request = hypervisor_service_pb2.BotIdRequest(bot_id=bot_id)
        try:
            pb = await self._stub.GetBotStatus(request, timeout=self._t(timeout))
            return BotStatusHV(pb.bot_id, pb.alive, pb.budget)
        except grpc.aio.AioRpcError as exc:
            if exc.code() == grpc.StatusCode.NOT_FOUND:
                return None
            self._handle_error("GetBotStatus", exc)
            return None

    async def list_bots(self, timeout: float | None = None) -> BotList:
        request = hypervisor_service_pb2.ListBotsRequest()
        try:
            pb = await self._stub.ListBots(request, timeout=self._t(timeout))
            return BotList(
                bots=[
                    BotStats(
                        bot_id=b.bot_id,
                        hypervisor_id=b.hypervisor_id,
                        points_left=b.points_left,
                        alive=True,
                    )
                    for b in pb.bots
                ]
            )
        except grpc.aio.AioRpcError as exc:
            self._handle_error("ListBots", exc)
            return BotList(bots=[])

    # ------------------------------------------------------------------
    # Control de presupuesto
    # ------------------------------------------------------------------

    async def reset_budgets(
        self,
        bot_ids: list[str],
        new_budgets: dict[str, int],
        default_budget: int = 100,
        timeout: float | None = None,
    ) -> bool:
        overrides = [
            common_pb2.BudgetEntry(bot_id=bid, budget=pts)
            for bid, pts in new_budgets.items()
            if pts != default_budget
        ]
        request = hypervisor_service_pb2.ResetBudgetsRequest(
            bot_ids=bot_ids,
            default_budget=default_budget,
            overrides=overrides,
        )
        try:
            pb = await self._stub.ResetBudgets(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.aio.AioRpcError as exc:
            self._handle_error("ResetBudgets", exc)
            return False

    async def set_point_budget(
        self, bot_id: str, points: int, timeout: float | None = None
    ) -> bool:
        request = hypervisor_service_pb2.SetPointBudgetRequest(
            bot_id=bot_id, points=points
        )
        try:
            pb = await self._stub.SetPointBudget(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.aio.AioRpcError as exc:
            self._handle_error("SetPointBudget", exc)
            return False

    # ------------------------------------------------------------------
    # Pausa / reanudación
    # ------------------------------------------------------------------

    async def freeze(self, timeout: float | None = None) -> bool:
        """Ordena al HV pausar todos sus bots. Espera confirmación."""
        request = hypervisor_service_pb2.FreezeRequest()
        try:
            pb = await self._stub.Freeze(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.aio.AioRpcError as exc:
            self._handle_error("Freeze", exc)
            return False

    async def resume(self, timeout: float | None = None) -> bool:
        """Ordena al HV reanudar sus bots."""
        request = hypervisor_service_pb2.ResumeRequest()
        try:
            pb = await self._stub.Resume(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.aio.AioRpcError as exc:
            self._handle_error("Resume", exc)
            return False

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    async def save_snapshot(
        self, snapshot_id: str, timeout: float | None = None
    ) -> bool:
        """Ordena al HV guardar su estado con el snapshot_id dado."""
        request = hypervisor_service_pb2.SaveSnapshotRequest(snapshot_id=snapshot_id)
        try:
            pb = await self._stub.SaveSnapshot(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.aio.AioRpcError as exc:
            self._handle_error("SaveSnapshot", exc)
            return False
