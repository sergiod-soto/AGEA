"""
gestor_client.py — Cliente gRPC del GestorService.

Usado por:
  - El Mundo       → SpawnBot, KillBot, UpdateFitness,
                      BuildFitnessReport, BroadcastBudgets
  - Los Hypervisores → RegisterHypervisor, UpdateHypervisorLoad,
                      ForwardAction

No contiene lógica de negocio; solo traducción protobuf ↔ Python
y gestión de errores gRPC.

Uso básico
----------
    from Hypervisores.Transporte.gestor_bots_client import GestorClient

    client = GestorBotsClient("localhost:50051")

    # El Mundo spawnea un bot
    info = client.spawn_bot(bot_id="bot_001", genome=b"...", budget=100)
    print(info.proxy_address)   # → "192.168.1.10:50053"

    # Un Hypervisor se registra
    client.register_hypervisor("hv_01", "192.168.1.10", 50052, 50053, capacity=32)

    # Un Hypervisor sube una acción
    result = client.forward_action("bot_001", "hv_01", "observe", payload=b"...")
"""

from __future__ import annotations

import logging
from typing import Optional

import grpc

from Gestores.Transporte.Proto_Generated import (
    common_pb2,
    gestor_bots_service_pb2,
    gestor_bots_service_pb2_grpc,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tipos de retorno simples (espejo de los de gestor.py, sin importarlo)
# ---------------------------------------------------------------------------


class BotInfo:
    __slots__ = ("bot_id", "hypervisor_id", "proxy_address", "ok", "error")

    def __init__(self, bot_id, hypervisor_id, proxy_address, ok, error):
        self.bot_id = bot_id
        self.hypervisor_id = hypervisor_id
        self.proxy_address = proxy_address
        self.ok = ok
        self.error = error

    def __repr__(self):
        return (
            f"BotInfo(bot_id={self.bot_id!r}, ok={self.ok}, "
            f"proxy={self.proxy_address!r}, error={self.error!r})"
        )


class ActionResult:
    __slots__ = ("ok", "payload", "error", "world_tick")

    def __init__(self, ok, payload, error, world_tick=0):
        self.ok = ok
        self.payload = payload
        self.error = error
        self.world_tick = world_tick

    def __repr__(self):
        return f"ActionResult(ok={self.ok}, error={self.error!r})"


class HypervisorInfo:
    __slots__ = (
        "hypervisor_id",
        "address",
        "port",
        "proxy_port",
        "capacity",
        "current_load",
        "online",
    )

    def __init__(
        self, hypervisor_id, address, port, proxy_port, capacity, current_load, online
    ):
        self.hypervisor_id = hypervisor_id
        self.address = address
        self.port = port
        self.proxy_port = proxy_port
        self.capacity = capacity
        self.current_load = current_load
        self.online = online


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------


class GestorClient:
    """
    Cliente gRPC del Gestor.

    Parámetros
    ----------
    address : str
        "host:puerto" del Gestor, p.ej. "localhost:50051".
    timeout : float
        Tiempo máximo de espera por RPC en segundos (default 10 s).
        Cada método acepta un timeout propio que sobreescribe este default.
    """

    def __init__(self, address: str, timeout: float = 10.0):
        self._address = address
        self._timeout = timeout

        # Canal gRPC reutilizable (thread-safe)
        self._channel = grpc.insecure_channel(
            address,
            options=[
                ("grpc.max_receive_message_length", 256 * 1024 * 1024),
                ("grpc.max_send_message_length", 256 * 1024 * 1024),
                ("grpc.keepalive_time_ms", 20_000),
                ("grpc.keepalive_timeout_ms", 10_000),
            ],
        )
        self._stub = gestor_bots_service_pb2_grpc.GestorServiceStub(self._channel)
        logger.info("GestorClient conectado a %s", address)

    def close(self):
        """Cierra el canal gRPC. Llamar al apagar el proceso."""
        self._channel.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _t(self, timeout: Optional[float]) -> float:
        """Devuelve el timeout efectivo: el del método o el del cliente."""
        return timeout if timeout is not None else self._timeout

    @staticmethod
    def _handle_grpc_error(method_name: str, exc: grpc.RpcError):
        logger.error(
            "%s falló: código=%s detalle=%s",
            method_name,
            exc.code(),
            exc.details(),
        )

    # ------------------------------------------------------------------
    # Ciclo de vida de bots (llamado por el Mundo)
    # ------------------------------------------------------------------

    def spawn_bot(
        self,
        bot_id: str,
        codigo_gz: bytes = b"",
        budget: int = 100,
        metadata: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> BotInfo:
        """
        Pide al Gestor que cree un bot en el Hypervisor más libre.

        codigo_gz: código Python compilado y comprimido con gzip.
                   El Mundo lo genera antes de llamar a este método.
        Devuelve BotInfo con proxy_address (host:puerto) al que el bot
        debe conectarse para hablar con el Mundo.
        """
        request = gestor_bots_service_pb2.SpawnBotRequest(
            config=common_pb2.BotConfig(
                bot_id=bot_id,
                codigo_gz=codigo_gz,
                budget=budget,
                metadata=metadata or {},
            )
        )
        try:
            pb = self._stub.SpawnBot(request, timeout=self._t(timeout))
            return BotInfo(
                pb.bot_id, pb.hypervisor_id, pb.proxy_address, pb.ok, pb.error
            )
        except grpc.RpcError as exc:
            self._handle_grpc_error("SpawnBot", exc)
            return BotInfo(bot_id, "", "", ok=False, error=str(exc))

    def kill_bot(self, bot_id: str, timeout: float | None = None) -> bool:
        """
        Elimina un bot. Devuelve True si el Gestor confirmó el kill.
        """
        request = gestor_bots_service_pb2.BotIdRequest(bot_id=bot_id)
        try:
            pb = self._stub.KillBot(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.RpcError as exc:
            self._handle_grpc_error("KillBot", exc)
            return False

    def update_fitness(
        self,
        bot_id: str,
        fitness: float,
        tick: int,
        timeout: float | None = None,
    ) -> bool:
        """El Mundo informa del fitness de un bot tras evaluar su acción."""
        request = gestor_bots_service_pb2.UpdateFitnessRequest(
            bot_id=bot_id, fitness=fitness, tick=tick
        )
        try:
            pb = self._stub.UpdateFitness(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.RpcError as exc:
            self._handle_grpc_error("UpdateFitness", exc)
            return False

    def broadcast_budgets(
        self,
        default_budget: int,
        overrides: dict[str, int] | None = None,
        timeout: float | None = None,
    ) -> bool:
        """
        Ordena al Gestor que resetee los presupuestos en todos los HVs.
        Se llama al inicio de cada ciclo evolutivo.

        overrides: {bot_id: presupuesto_especial}
        """
        budget_entries = [
            common_pb2.BudgetEntry(bot_id=bid, budget=pts)
            for bid, pts in (overrides or {}).items()
        ]
        request = gestor_bots_service_pb2.BroadcastBudgetsRequest(
            default_budget=default_budget,
            overrides=budget_entries,
        )
        try:
            pb = self._stub.BroadcastBudgets(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.RpcError as exc:
            self._handle_grpc_error("BroadcastBudgets", exc)
            return False

    # ------------------------------------------------------------------
    # Registro y control de Hypervisores (llamado por cada Hypervisor)
    # ------------------------------------------------------------------

    def register_hypervisor(
        self,
        hypervisor_id: str,
        address: str,
        port: int,
        proxy_port: int,
        capacity: int,
        timeout: float | None = None,
    ) -> bool:
        """
        Un Hypervisor se anuncia al Gestor al arrancar.
        Devuelve True si el registro fue aceptado.
        """
        request = gestor_bots_service_pb2.RegisterHypervisorRequest(
            hypervisor_id=hypervisor_id,
            address=address,
            port=port,
            proxy_port=proxy_port,
            capacity=capacity,
        )
        try:
            pb = self._stub.RegisterHypervisor(request, timeout=self._t(timeout))
            if pb.ok:
                logger.info(
                    "Hypervisor %s registrado correctamente en el Gestor.",
                    hypervisor_id,
                )
            else:
                logger.warning("Registro de %s rechazado: %s", hypervisor_id, pb.error)
            return pb.ok
        except grpc.RpcError as exc:
            self._handle_grpc_error("RegisterHypervisor", exc)
            return False

    def update_hypervisor_load(
        self,
        hypervisor_id: str,
        current_load: int,
        timeout: float | None = None,
    ) -> bool:
        """El Hypervisor informa de cuántos bots tiene activos ahora."""
        request = gestor_bots_service_pb2.UpdateLoadRequest(
            hypervisor_id=hypervisor_id,
            current_load=current_load,
        )
        try:
            pb = self._stub.UpdateHypervisorLoad(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.RpcError as exc:
            self._handle_grpc_error("UpdateHypervisorLoad", exc)
            return False

    def list_hypervisors(self, timeout: float | None = None) -> list[HypervisorInfo]:
        """Devuelve la lista de todos los Hypervisores conocidos por el Gestor."""
        request = gestor_bots_service_pb2.ListHypervisorsRequest()
        try:
            pb = self._stub.ListHypervisors(request, timeout=self._t(timeout))
            return [
                HypervisorInfo(
                    hv.hypervisor_id,
                    hv.address,
                    hv.port,
                    hv.proxy_port,
                    hv.capacity,
                    hv.current_load,
                    hv.online,
                )
                for hv in pb.hypervisors
            ]
        except grpc.RpcError as exc:
            self._handle_grpc_error("ListHypervisors", exc)
            return []

    # ------------------------------------------------------------------
    # Reenvío de acciones al Mundo (llamado por el Hypervisor)
    # ------------------------------------------------------------------

    def forward_action(
        self,
        bot_id: str,
        hypervisor_id: str,
        action_type: str,
        payload: bytes = b"",
        timeout: float | None = None,
    ) -> ActionResult:
        """
        El Hypervisor sube aquí la acción de un bot (ya validada en puntos).
        El Gestor la reenvía al Mundo y devuelve el resultado.

        action_type: "observe" | "move" | "rotate" | "interact"
        payload: bytes opacos que el Mundo interpreta según action_type
        """
        request = gestor_bots_service_pb2.ForwardActionRequest(
            bot_id=bot_id,
            hypervisor_id=hypervisor_id,
            action_type=action_type,
            payload=payload,
        )
        try:
            pb = self._stub.ForwardAction(request, timeout=self._t(timeout))
            return ActionResult(pb.ok, pb.payload, pb.error, pb.world_tick)
        except grpc.RpcError as exc:
            self._handle_grpc_error("ForwardAction", exc)
            return ActionResult(ok=False, payload=b"", error=str(exc))
