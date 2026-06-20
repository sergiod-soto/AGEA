"""
hypervisor.py — Lógica pura del Hypervisor.
"""

from __future__ import annotations

import gzip
import logging
import os
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil

from Gestores.Mundo.Gestor_Mundo.gestor_mundo import ActionResult

logger = logging.getLogger(__name__)

DEFAULT_BUDGET = 100


# ---------------------------------------------------------------------------
# Tipos internos
# ---------------------------------------------------------------------------


@dataclass
class BotRecord:
    bot_id: str
    budget: int
    max_budget: int
    alive: bool = True


@dataclass
class SpawnResult:
    ok: bool
    error: str = ""


# ---------------------------------------------------------------------------
# Hypervisor
# ---------------------------------------------------------------------------


class Hypervisor:
    """
    Proxy transparente entre los Bots y el Mundo.

    Parámetros
    ----------
    hypervisor_id   : str
    gestor_client   : GestorBotsClient
    capacity        : int
    my_address      : str
    my_port         : int
    my_proxy_port   : int
    """

    def __init__(
        self,
        hypervisor_id: str,
        gestor_client,
        gestor_mundo_client,
        capacity: int = 32,
        my_address: str = "localhost",
        my_port: int = 50052,
        my_proxy_port: int = 50053,
    ):
        self.hypervisor_id = hypervisor_id
        self.gestor_client = gestor_client
        self.gestor_mundo_client = gestor_mundo_client
        self.capacity = capacity
        self._my_address = my_address
        self._my_port = my_port
        self._my_proxy_port = my_proxy_port

        self._lock = threading.Lock()
        self._bots: dict[str, BotRecord] = {}
        self._procesos: dict[str, subprocess.Popen] = {}

        self._delegated: set[str] = set()

        logger.info(
            "Hypervisor %s inicializado (cap=%d, proxy=%s:%d)",
            hypervisor_id,
            capacity,
            my_address,
            my_proxy_port,
        )

    # ------------------------------------------------------------------
    # Acciones delegadas
    # ------------------------------------------------------------------

    def set_delegated_actions(self, action_names: list[str]) -> None:
        if not action_names:
            logger.info("HV %s: sin acciones delegadas.", self.hypervisor_id)
            self._delegated = set()
            return

        try:
            from Gestores.Mundo.api_acciones import ACCIONES
        except ImportError as exc:
            logger.error(
                "No se pudo importar acciones: %s. "
                "El HV no interceptará ninguna acción.", exc,
            )
            self._delegated = set()
            return

        validadas = set()
        for name in action_names:
            if name not in ACCIONES:
                logger.warning(
                    "Acción delegada '%s' no encontrada en ACCIONES; ignorada.", name
                )
                continue
            validadas.add(name)

        self._delegated = validadas
        logger.info(
            "HV %s: acciones delegadas → %s",
            self.hypervisor_id, self._delegated,
        )

    def is_delegated(self, action_name: str) -> bool:
        """True si la acción se ejecuta localmente en este HV."""
        return action_name in self._delegated

    def execute_delegated(
        self, bot_id: str, action_name: str, payload: bytes
    ) -> ActionResult:
        fn = self._delegated.get(action_name)
        if fn is None:
            return ActionResult(
                ok=False, error=f"Acción '{action_name}' no está delegada en este HV."
            )

        with self._lock:
            if bot_id not in self._bots:
                return ActionResult(ok=False, error=f"Bot {bot_id!r} no encontrado.")

        from Gestores.Mundo.api_acciones import AccionContext

        ctx = AccionContext(bot_id=bot_id, payload=payload)

        try:
            return fn(ctx)
        except Exception as exc:
            logger.error(
                "Error ejecutando acción delegada '%s' para bot %s: %s",
                action_name,
                bot_id,
                exc,
            )
            return ActionResult(ok=False, error=str(exc))

    # ------------------------------------------------------------------
    # Registro en el Gestor
    # ------------------------------------------------------------------

    def register_with_gestor(self) -> bool:
        """
        Llama a RegisterHypervisor en el Gestor y construye
        la tabla de interceptación con la lista recibida.
        Devuelve True si el Gestor aceptó el registro.
        """
        result = self.gestor_client.register_hypervisor(
            hypervisor_id=self.hypervisor_id,
            address=self._my_address,
            port=self._my_port,
            proxy_port=self._my_proxy_port,
            capacity=self.capacity,
        )

        if result.ok:
            self.set_delegated_actions(result.delegated_actions)
            logger.info(
                "HV %s registrado correctamente en el Gestor.", self.hypervisor_id
            )
        else:
            logger.error(
                "El Gestor rechazó el registro del HV %s: %s",
                self.hypervisor_id,
                result.error,
            )

        return result.ok

    def report_load(self) -> None:
        with self._lock:
            load = len(self._bots)
        self.gestor_client.update_hypervisor_load(self.hypervisor_id, load)

    # ------------------------------------------------------------------
    # Ciclo de vida de bots
    # ------------------------------------------------------------------

    def spawn_bot(self, config: dict) -> SpawnResult:
        bot_id = config.get("bot_id", "")
        codigo_gz = config.get("codigo_gz", b"")
        budget = int(config.get("budget", DEFAULT_BUDGET))

        if not bot_id:
            return SpawnResult(ok=False, error="bot_id vacío")

        # Comprobar capacidad antes de escribir en disco
        with self._lock:
            if len(self._bots) >= self.capacity:
                return SpawnResult(ok=False, error="Hypervisor a plena capacidad")
            if bot_id in self._bots:
                logger.warning("spawn_bot: bot %s ya existe; sobreescribiendo.", bot_id)

        # Escribir código en disco fuera del lock
        codigo_path = self._codigo_path(bot_id)
        try:
            codigo_path.parent.mkdir(parents=True, exist_ok=True)
            codigo_path.write_bytes(gzip.decompress(codigo_gz))
        except Exception as exc:
            logger.error("Error escribiendo código de bot %s: %s", bot_id, exc)
            return SpawnResult(ok=False, error=f"Error descomprimiendo código: {exc}")

        # Lanzar proceso fuera del lock
        try:
            proceso = subprocess.Popen(
                ["python", str(codigo_path)],
                env={
                    **os.environ,
                    "BOT_ID": bot_id,
                    "HV_PROXY_ADDRESS": f"{self._my_address}:{self._my_proxy_port}",
                },
            )
        except Exception as exc:
            codigo_path.unlink(missing_ok=True)
            logger.error("Error lanzando proceso bot %s: %s", bot_id, exc)
            return SpawnResult(ok=False, error=f"Error lanzando proceso: {exc}")

        # Solo adquirir lock para actualizar estado
        with self._lock:
            self._bots[bot_id] = BotRecord(
                bot_id=bot_id, budget=budget, max_budget=budget
            )
            self._procesos[bot_id] = proceso

        logger.info("Bot %s spawneado (budget=%d).", bot_id, budget)
        return SpawnResult(ok=True)

    def _codigo_path(self, bot_id: str) -> Path:
        return Path("bots_codigo") / self.hypervisor_id / f"{bot_id}.py"

    def kill_bot(self, bot_id: str) -> None:
        with self._lock:
            if bot_id not in self._bots:
                logger.warning("kill_bot: bot desconocido %s", bot_id)
                return
            del self._bots[bot_id]
            proceso = self._procesos.pop(bot_id, None)

        if proceso is not None:
            try:
                proceso.terminate()
            except Exception as exc:
                logger.warning("No se pudo terminar proceso de %s: %s", bot_id, exc)

        try:
            self._codigo_path(bot_id).unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("No se pudo eliminar código de %s: %s", bot_id, exc)

        logger.info("Bot %s eliminado.", bot_id)

    # ------------------------------------------------------------------
    # Control de presupuesto
    # ------------------------------------------------------------------

    def try_spend_points(self, bot_id: str, cost: int) -> tuple[bool, int]:
        with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                logger.warning("try_spend_points: bot desconocido %s", bot_id)
                return False, 0
            if not rec.alive:
                return False, 0
            if rec.budget < cost:
                logger.debug(
                    "Bot %s sin puntos: tiene %d, necesita %d.",
                    bot_id,
                    rec.budget,
                    cost,
                )
                return False, rec.budget
            rec.budget -= cost
            logger.debug(
                "Bot %s gastó %d pt(s). Restantes: %d.", bot_id, cost, rec.budget
            )
            return True, rec.budget

    def set_point_budget(self, bot_id: str, points: int) -> None:
        with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                logger.warning("set_point_budget: bot desconocido %s", bot_id)
                return
            rec.budget = rec.max_budget = points

    def reset_budgets(self, bot_ids: list[str], new_budgets: dict[str, int]) -> None:
        with self._lock:
            for bot_id in bot_ids:
                rec = self._bots.get(bot_id)
                if rec is None:
                    continue
                rec.budget = rec.max_budget = new_budgets.get(bot_id, rec.max_budget)
        logger.info(
            "Budgets reseteados para %d bot(s) en HV %s.",
            len(bot_ids),
            self.hypervisor_id,
        )

    # ------------------------------------------------------------------
    # Proxy al Mundo
    # ------------------------------------------------------------------

    def forward_to_gestor(self, bot_id: str, action_type: str, payload: bytes):
        return self.gestor_client.forward_action(
            bot_id=bot_id,
            hypervisor_id=self.hypervisor_id,
            action_type=action_type,
            payload=payload,
        )

    # ------------------------------------------------------------------
    # Métricas de sistema
    # ------------------------------------------------------------------

    def get_system_load(self) -> dict:
        def _is_aws() -> bool:
            return "AWS_BATCH_JOB_ID" in os.environ

        mem = psutil.virtual_memory()
        base = {
            "mem_percent": mem.percent,
            "mem_used_mb": round(mem.used / 1024 / 1024),
            "mem_total_mb": round(mem.total / 1024 / 1024),
            "bot_count": len(self._bots),
        }

        if _is_aws():
            try:
                quota, period = open("/sys/fs/cgroup/cpu.max").read().split()
                cpu = (
                    100.0
                    if quota == "max"
                    else round(int(quota) / int(period) * 100, 1)
                )
            except Exception:
                cpu = psutil.cpu_percent(interval=None)
            return {**base, "cpu_percent": cpu, "source": "aws"}

        return {
            **base,
            "cpu_percent": psutil.cpu_percent(interval=None),
            "source": "local",
        }

    # ------------------------------------------------------------------
    # Persistencia (stubs)
    # ------------------------------------------------------------------

    def guardar_estado(self):
        raise NotImplementedError

    def cargar_estado(self):
        raise NotImplementedError
