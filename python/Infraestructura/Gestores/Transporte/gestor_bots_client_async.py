# Infraestructura/Gestores/Transporte/gestor_bots_client_async.py
"""
gestor_bots_client_async.py — Cliente async gRPC hacia Gestor_Bots.

Existe por separado de gestor_bots_client.py (síncrono) porque ambos
tienen consumidores con modelos de concurrencia distintos:
  - gestor_bots_client.py (síncrono)  → ya no lo usa Hypervisor (migrado
    a asyncio) — queda como cliente síncrono disponible por si algún
    otro consumidor síncrono lo necesitara en el futuro.
  - Este cliente (async)              → usado por Logica_Mundo,
    Comunicaciones_Remoto, e Hypervisor (tras la migración a asyncio),
    todos enteramente asyncio.

AMPLIADO: se añaden register_hypervisor, update_hypervisor_load,
notificar_avatar_sin_piloto y forward_action — los métodos que
Hypervisor necesita y que faltaban aquí (antes solo estaban en la
versión síncrona, porque Hypervisor no usaba este cliente todavía).
Las firmas replican exactamente las de gestor_bots_client.py para no
introducir ninguna diferencia de comportamiento entre ambas versiones.

RegistroHVResult se importa desde gestor_bots_client.py en vez de
duplicar la dataclass — es un tipo de dato puro, sin lógica síncrona,
así que no hay motivo para tener dos definiciones de lo mismo.
"""

from __future__ import annotations

import logging
from typing import Optional

import grpc.aio

from Infraestructura.Gestores.tipos_comunes import (
    ActionResult,
    HypervisorInfo,
    HypervisorList,
)
from Infraestructura.Gestores.Transporte.gestor_bots_client import RegistroHVResult
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
    # Añadido: Flujo B (el HV detecta que el script se rompió)
    # ------------------------------------------------------------------

    async def notificar_avatar_sin_piloto(
        self, bot_id: str, timeout: float | None = None
    ) -> bool:
        """
        Flujo B: llamado por Hypervisor cuando detecta que el script de
        un bot se ha roto (no compila, excepción no controlada, o el
        proceso terminó inesperadamente — ver Hypervisor._watch_bot_process).
        El HV no mata su propio proceso a través de este método — eso ya
        lo gestiona localmente. Aquí solo se notifica para que
        Logica_Mundo elimine el avatar correspondiente en el gold.
        """
        await self._ensure_channel()
        request = gestor_bots_service_pb2.BotIdRequest(bot_id=bot_id)
        try:
            resp = await self._stub.NotificarAvatarSinPiloto(
                request, timeout=self._t(timeout)
            )
            return resp.ok
        except grpc.aio.AioRpcError as exc:
            logger.error("NotificarAvatarSinPiloto falló para bot %s: %s", bot_id, exc)
            return False

    # ------------------------------------------------------------------
    # Añadido: Registro de Hypervisores
    # ------------------------------------------------------------------

    async def register_hypervisor(
        self,
        hypervisor_id: str,
        address: str,
        port: int,
        proxy_port: int,
        capacity: int,
        timeout: float | None = None,
    ) -> RegistroHVResult:
        """
        El Hypervisor se anuncia al Gestor al arrancar. Ver
        RegistroHVResult en gestor_bots_client.py — delegated_actions se
        mantiene en la respuesta por compatibilidad con el proto, aunque
        Hypervisor ya no lo usa (mecanismo de acciones delegadas retirado).
        """
        await self._ensure_channel()
        request = gestor_bots_service_pb2.RegisterHypervisorRequest(
            hypervisor_id=hypervisor_id,
            address=address,
            port=port,
            proxy_port=proxy_port,
            capacity=capacity,
        )
        try:
            resp = await self._stub.RegisterHypervisor(
                request, timeout=self._t(timeout)
            )
            if resp.ok:
                logger.info("HV %s registrado.", hypervisor_id)
            else:
                logger.warning(
                    "Registro de %s rechazado: %s", hypervisor_id, resp.error
                )
            return RegistroHVResult(
                ok=resp.ok,
                error=resp.error,
                delegated_actions=list(resp.delegated_actions),
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("RegisterHypervisor falló para %s: %s", hypervisor_id, exc)
            return RegistroHVResult(ok=False, error=str(exc))

    async def update_hypervisor_load(
        self,
        hypervisor_id: str,
        current_load: int,
        timeout: float | None = None,
    ) -> bool:
        await self._ensure_channel()
        request = gestor_bots_service_pb2.UpdateLoadRequest(
            hypervisor_id=hypervisor_id,
            current_load=current_load,
        )
        try:
            resp = await self._stub.UpdateHypervisorLoad(
                request, timeout=self._t(timeout)
            )
            return resp.ok
        except grpc.aio.AioRpcError as exc:
            logger.error("UpdateHypervisorLoad falló para %s: %s", hypervisor_id, exc)
            return False

    # ------------------------------------------------------------------
    # Añadido: Reenvío de acciones al Mundo (usado por Hypervisor)
    # ------------------------------------------------------------------

    async def forward_action(
        self,
        bot_id: str,
        hypervisor_id: str,
        action_type: str,
        payload: bytes = b"",
        timeout: float | None = None,
    ) -> ActionResult:
        await self._ensure_channel()
        request = gestor_bots_service_pb2.ForwardActionRequest(
            bot_id=bot_id,
            hypervisor_id=hypervisor_id,
            action_type=action_type,
            payload=payload,
        )
        try:
            resp = await self._stub.ForwardAction(request, timeout=self._t(timeout))
            return ActionResult(resp.ok, resp.payload, resp.error, resp.world_tick)
        except grpc.aio.AioRpcError as exc:
            logger.error("ForwardAction falló para bot %s: %s", bot_id, exc)
            return ActionResult(ok=False, payload=b"", error=str(exc))

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
