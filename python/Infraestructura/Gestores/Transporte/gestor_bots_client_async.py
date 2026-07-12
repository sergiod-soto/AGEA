# Infraestructura/Gestores/Transporte/gestor_bots_client_async.py
"""
gestor_bots_client_async.py — Cliente async gRPC hacia Gestor_Bots.

Existe por separado de gestor_bots_client.py (síncrono) porque ambos
tienen consumidores con modelos de concurrencia distintos:
  - gestor_bots_client.py (síncrono)  → usado por Hypervisor, que corre
    sobre grpc.server (ThreadPoolExecutor), no asyncio.
  - Este cliente (async)              → usado por Logica_Mundo y por
    Comunicaciones_Remoto, ambos enteramente asyncio (grpc.aio.server).
    Una llamada síncrona bloqueante dentro de un método async
    bloquearía el event loop durante esa llamada de red — de ahí la
    necesidad de esta versión.

Ampliado con las operaciones de monitorización/administración que
Comunicaciones_Remoto reenvía cuando Comunicaciones_Local se lo pide
(destino GESTOR_BOTS del puente Ejecutar): list_hypervisors,
broadcast_budgets, freeze_all, resume_all, save_snapshot.
"""

from __future__ import annotations

import logging
from typing import Optional

import grpc.aio

from Infraestructura.Gestores.tipos_comunes import HypervisorInfo, HypervisorList
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2,
)

logger = logging.getLogger(__name__)


class GestorBotsClientAsync:
    """
    Cliente async gRPC del Gestor de Bots.

    Parámetros
    ----------
    address : str   "host:puerto"
    timeout : float segundos de espera por RPC (default 10 s)
    """

    def __init__(self, address: str, timeout: float = 10.0):
        self._address = address
        self._timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub = None

    async def _ensure_channel(self) -> None:
        """Conexión perezosa — misma razón que en gestor_mundo_client.py:
        evita fallos de arranque si Gestor_Bots tarda unos segundos más
        en estar listo que quien lo consume."""
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(self._address)
            self._stub = gestor_bots_service_pb2_grpc.GestorBotsServiceStub(
                self._channel
            )

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None

    def _t(self, timeout: Optional[float]) -> float:
        return timeout if timeout is not None else self._timeout

    # ------------------------------------------------------------------
    # Muerte de bots — Flujo A (el Mundo decide la muerte)
    # ------------------------------------------------------------------

    async def matar_script_bot(self, bot_id: str, timeout: float | None = None) -> bool:
        """
        Pide a Gestor_Bots que mate el proceso/script de un bot cuyo
        avatar ya fue eliminado del gold por Logica_Mundo. No lleva
        cause/tick: el origen es siempre "el Mundo decidió la muerte",
        sin necesidad de distinguir el motivo en este punto (el motivo
        ya se registró en logica_mundo.matar_bot).
        """
        await self._ensure_channel()
        request = gestor_bots_service_pb2.BotIdRequest(bot_id=bot_id)
        try:
            resp = await self._stub.MatarScriptBot(request, timeout=self._t(timeout))
            return resp.ok
        except grpc.aio.AioRpcError as exc:
            logger.error("MatarScriptBot falló para bot %s: %s", bot_id, exc)
            return False

    # ------------------------------------------------------------------
    # Monitorización / administración (usado por Comunicaciones_Remoto)
    # ------------------------------------------------------------------

    async def list_hypervisors(self, timeout: float | None = None) -> HypervisorList:
        await self._ensure_channel()
        try:
            resp = await self._stub.ListHypervisors(
                gestor_bots_service_pb2.ListHypervisorsRequest(),
                timeout=self._t(timeout),
            )
            return HypervisorList(
                hypervisors=[
                    HypervisorInfo(
                        hypervisor_id=hv.hypervisor_id,
                        address=hv.address,
                        port=hv.port,
                        proxy_port=hv.proxy_port,
                        capacity=hv.capacity,
                        current_load=hv.current_load,
                        online=hv.online,
                    )
                    for hv in resp.hypervisors
                ]
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("ListHypervisors falló: %s", exc)
            return HypervisorList(hypervisors=[])

    async def broadcast_budgets(
        self,
        default_budget: int,
        overrides: dict[str, int] | None = None,
        timeout: float | None = None,
    ) -> bool:
        budget_entries = [
            common_pb2.BudgetEntry(bot_id=bid, budget=pts)
            for bid, pts in (overrides or {}).items()
        ]
        request = gestor_bots_service_pb2.BroadcastBudgetsRequest(
            default_budget=default_budget,
            overrides=budget_entries,
        )
        try:
            await self._ensure_channel()
            resp = await self._stub.BroadcastBudgets(request, timeout=self._t(timeout))
            return resp.ok
        except grpc.aio.AioRpcError as exc:
            logger.error("BroadcastBudgets falló: %s", exc)
            return False

    async def freeze_all(self, timeout: float | None = None) -> bool:
        await self._ensure_channel()
        try:
            resp = await self._stub.FreezeAll(
                gestor_bots_service_pb2.FreezeAllRequest(), timeout=self._t(timeout)
            )
            return resp.ok
        except grpc.aio.AioRpcError as exc:
            logger.error("FreezeAll falló: %s", exc)
            return False

    async def resume_all(self, timeout: float | None = None) -> bool:
        await self._ensure_channel()
        try:
            resp = await self._stub.ResumeAll(
                gestor_bots_service_pb2.ResumeAllRequest(), timeout=self._t(timeout)
            )
            return resp.ok
        except grpc.aio.AioRpcError as exc:
            logger.error("ResumeAll falló: %s", exc)
            return False

    async def save_snapshot(
        self, snapshot_id: str, timeout: float | None = None
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        request = gestor_bots_service_pb2.SaveSnapshotRequest(snapshot_id=snapshot_id)
        try:
            resp = await self._stub.SaveSnapshot(request, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("SaveSnapshot falló: %s", exc)
            return False, str(exc)
