"""
hypervisor_client.py — Cliente gRPC del HypervisorService.

Usado exclusivamente por el Gestor para dar órdenes a un Hypervisor concreto.
Se crea una instancia por cada HV que se registra en el Gestor.

Uso básico
----------
    from Hypervisores.Transporte.hypervisor_client import HypervisorClient

    # El Gestor lo crea al recibir RegisterHypervisor
    client = HypervisorClient("192.168.1.10", 50052)

    # Ordena crear un bot en ese HV
    info = client.spawn_bot({"bot_id": "bot_001", "budget": 100, "genome": b"..."})

    # Al inicio de cada ciclo
    client.reset_budgets(["bot_001", "bot_002"], {"bot_001": 150, "bot_002": 100})

    # Al terminar
    client.close()
"""

from __future__ import annotations

import logging
from typing import Optional

import grpc

from Gestores.Transporte.Proto_Generated.Bots import (
    common_pb2,
    hypervisor_service_pb2,
    hypervisor_service_pb2_grpc,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tipos de retorno (espejo ligero de los de hypervisor.py)
# ---------------------------------------------------------------------------

class BotInfo:
    __slots__ = ("bot_id", "hypervisor_id", "ok", "error")

    def __init__(self, bot_id, hypervisor_id, ok, error):
        self.bot_id        = bot_id
        self.hypervisor_id = hypervisor_id
        self.ok            = ok
        self.error         = error

    def __repr__(self):
        return (f"BotInfo(bot_id={self.bot_id!r}, ok={self.ok}, "
                f"error={self.error!r})")


class BotStats:
    __slots__ = ("bot_id", "hypervisor_id", "points_left", "alive", "uptime_s")

    def __init__(self, bot_id, hypervisor_id, points_left, alive, uptime_s=0.0):
        self.bot_id        = bot_id
        self.hypervisor_id = hypervisor_id
        self.points_left   = points_left
        self.alive         = alive
        self.uptime_s      = uptime_s


class BotStatus:
    __slots__ = ("bot_id", "alive", "budget")

    def __init__(self, bot_id, alive, budget):
        self.bot_id = bot_id
        self.alive  = alive
        self.budget = budget


class BotList:
    __slots__ = ("bots",)

    def __init__(self, bots):
        self.bots = bots   # list[BotStats]


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------

class HypervisorClient:
    """
    Cliente gRPC del HypervisorService.

    Parámetros
    ----------
    address : str
        Host del Hypervisor (sin puerto).
    port : int
        Puerto del HypervisorService en ese host.
    timeout : float
        Timeout por defecto para cada RPC en segundos (default 10 s).
    """

    def __init__(self, address: str, port: int, timeout: float = 10.0):
        self._address = address
        self._port    = port
        self._timeout = timeout
        self._target  = f"{address}:{port}"

        self._channel = grpc.insecure_channel(
            self._target,
            options=[
                ("grpc.max_receive_message_length", 256 * 1024 * 1024),
                ("grpc.max_send_message_length",    256 * 1024 * 1024),
                ("grpc.keepalive_time_ms",          20_000),
                ("grpc.keepalive_timeout_ms",       10_000),
            ],
        )
        self._stub = hypervisor_service_pb2_grpc.HypervisorServiceStub(self._channel)
        logger.info("HypervisorClient conectado a %s", self._target)

    def close(self):
        self._channel.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _t(self, timeout: Optional[float]) -> float:
        return timeout if timeout is not None else self._timeout

    def _handle_error(self, method: str, exc: grpc.RpcError):
        logger.error(
            "%s → %s falló: código=%s detalle=%s",
            self._target, method, exc.code(), exc.details(),
        )

    # ------------------------------------------------------------------
    # Ciclo de vida de bots
    # ------------------------------------------------------------------

    def spawn_bot(
        self,
        bot_config: dict,
        timeout: float | None = None,
    ) -> BotInfo:
        """
        Ordena al HV que registre un bot localmente.

        bot_config espera:
          - "bot_id"  : str
          - "genome"  : bytes  (opcional)
          - "budget"  : int    (opcional, default 100)
          - "metadata": dict[str,str]  (opcional)
        """
        cfg = common_pb2.BotConfig(
            bot_id=bot_config.get("bot_id", ""),
            codigo_gz=bot_config.get("codigo_gz", b""),
            budget=int(bot_config.get("budget", 100)),
            metadata=bot_config.get("metadata", {}),
        )
        request = hypervisor_service_pb2.SpawnBotRequest(config=cfg)

        try:
            pb = self._stub.SpawnBot(request, timeout=self._t(timeout))
            return BotInfo(pb.bot_id, pb.hypervisor_id, pb.ok, pb.error)
        except grpc.RpcError as exc:
            self._handle_error("SpawnBot", exc)
            return BotInfo(
                bot_id=bot_config.get("bot_id", ""),
                hypervisor_id="",
                ok=False,
                error=str(exc),
            )

    def kill_bot(self, bot_id: str, timeout: float | None = None) -> bool:
        """Ordena al HV eliminar un bot. Devuelve True si fue aceptado."""
        request = hypervisor_service_pb2.BotIdRequest(bot_id=bot_id)
        try:
            pb = self._stub.KillBot(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.RpcError as exc:
            self._handle_error("KillBot", exc)
            return False

    def get_bot_stats(
        self,
        bot_id: str,
        timeout: float | None = None,
    ) -> Optional[BotStats]:
        """
        Devuelve el estado completo de un bot en el HV.
        Devuelve None si el bot no existe o hay error de red.
        """
        request = hypervisor_service_pb2.BotIdRequest(bot_id=bot_id)
        try:
            pb = self._stub.GetBotStats(request, timeout=self._t(timeout))
            return BotStats(
                bot_id=pb.bot_id,
                hypervisor_id=pb.hypervisor_id,
                points_left=pb.points_left,
                alive=True,   # si responde, el bot existe y está vivo
            )
        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.NOT_FOUND:
                return None
            self._handle_error("GetBotStats", exc)
            return None

    def get_bot_status(
        self,
        bot_id: str,
        timeout: float | None = None,
    ) -> Optional[BotStatus]:
        """
        Versión ligera: solo alive + puntos restantes.
        Devuelve None si el bot no existe o hay error.
        """
        request = hypervisor_service_pb2.BotIdRequest(bot_id=bot_id)
        try:
            pb = self._stub.GetBotStatus(request, timeout=self._t(timeout))
            return BotStatus(pb.bot_id, pb.alive, pb.budget)
        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.NOT_FOUND:
                return None
            self._handle_error("GetBotStatus", exc)
            return None

    def list_bots(self, timeout: float | None = None) -> BotList:
        """Lista todos los bots activos en el HV."""
        request = hypervisor_service_pb2.ListBotsRequest()
        try:
            pb = self._stub.ListBots(request, timeout=self._t(timeout))
            bots = [
                BotStats(
                    bot_id=b.bot_id,
                    hypervisor_id=b.hypervisor_id,
                    points_left=b.points_left,
                    alive=True,
                )
                for b in pb.bots
            ]
            return BotList(bots=bots)
        except grpc.RpcError as exc:
            self._handle_error("ListBots", exc)
            return BotList(bots=[])

    # ------------------------------------------------------------------
    # Control de presupuesto
    # ------------------------------------------------------------------

    def reset_budgets(
        self,
        bot_ids: list[str],
        new_budgets: dict[str, int],
        default_budget: int = 100,
        timeout: float | None = None,
    ) -> bool:
        """
        Resetea los presupuestos de puntos al inicio de cada ciclo.

        bot_ids      : lista de bots de este HV a resetear.
        new_budgets  : {bot_id: puntos} — si un bot no aparece, recibe default_budget.
        default_budget: presupuesto para los bots sin override explícito.

        Devuelve True si el HV confirmó el reset.
        """
        # Separamos los overrides del default para construir el mensaje
        overrides = [
            common_pb2.BudgetEntry(bot_id=bid, budget=pts)
            for bid, pts in new_budgets.items()
            if pts != default_budget   # solo mandamos los que difieren del default
        ]

        request = hypervisor_service_pb2.ResetBudgetsRequest(
            bot_ids=bot_ids,
            default_budget=default_budget,
            overrides=overrides,
        )

        try:
            pb = self._stub.ResetBudgets(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.RpcError as exc:
            self._handle_error("ResetBudgets", exc)
            return False

    def set_point_budget(
        self,
        bot_id: str,
        points: int,
        timeout: float | None = None,
    ) -> bool:
        """
        Ajusta el presupuesto de un bot concreto fuera de ciclo.
        Útil para penalizaciones o recompensas puntuales desde el Gestor.
        """
        request = hypervisor_service_pb2.SetPointBudgetRequest(
            bot_id=bot_id,
            points=points,
        )
        try:
            pb = self._stub.SetPointBudget(request, timeout=self._t(timeout))
            return pb.ok
        except grpc.RpcError as exc:
            self._handle_error("SetPointBudget", exc)
            return False
