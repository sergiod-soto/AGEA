"""
hypervisor.py — Lógica pura del Hypervisor.

Cambios respecto a la versión anterior:
  - HVContext: contexto que se pasa a las funciones delegadas.
  - set_delegated_actions(): construye la tabla de interceptación
    a partir de la lista de nombres recibida del Gestor al registrarse.
  - execute_delegated(): ejecuta una acción delegada localmente.
  - register_with_gestor(): consume RegistroHVResult y llama a
    set_delegated_actions() en el mismo paso.
"""

from __future__ import annotations

import gzip
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import psutil

logger = logging.getLogger(__name__)

ACTION_COSTS: dict[str, int] = {}
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
    spawned_at: float = field(default_factory=time.time)
    last_action: float = 0.0


@dataclass
class BotInfo:
    bot_id: str
    hypervisor_id: str
    ok: bool = True
    error: str = ""


@dataclass
class BotStats:
    bot_id: str
    hypervisor_id: str
    points_left: int
    alive: bool
    uptime_s: float


@dataclass
class BotStatus:
    bot_id: str
    alive: bool
    budget: int


@dataclass
class BotList:
    bots: list[BotStats]


@dataclass
class Entity:
    entity_id: str
    type: str
    x: float
    y: float
    rotation: float
    health: float
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class ActionResult:
    """Resultado de una acción, delegada o reenviada al Mundo."""

    ok: bool
    payload: bytes = b""
    error: str = ""


# ---------------------------------------------------------------------------
# Contexto para funciones delegadas
# ---------------------------------------------------------------------------


@dataclass
class HVContext:
    """
    Contexto que el Hypervisor pasa a cada función delegada al ejecutarla.

    Contiene todo lo que la función puede necesitar sin exponer el HV entero.
    A medida que el sistema crezca (sectores, etc.) se añaden campos aquí;
    las firmas de las funciones delegadas no cambian.

    Campos actuales
    ---------------
    bot_id     : identificador del bot que realiza la acción.
    bot_record : estado local del bot (budget, alive, etc.).
    payload    : bytes del request tal como los envió el bot.

    Campos futuros (TODO)
    ---------------------
    sector_client : cliente gRPC al sector donde reside el bot.
                    Se añadirá cuando exista comunicación HV↔Sector.
    """

    bot_id: str
    bot_record: BotRecord
    payload: bytes
    # sector_client: SectorClient | None = None  # TODO: sectores


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
        capacity: int = 32,
        my_address: str = "localhost",
        my_port: int = 50052,
        my_proxy_port: int = 50053,
    ):
        self.hypervisor_id = hypervisor_id
        self.gestor_client = gestor_client
        self.capacity = capacity
        self._my_address = my_address
        self._my_port = my_port
        self._my_proxy_port = my_proxy_port

        self._lock = threading.Lock()
        self._bots: dict[str, BotRecord] = {}

        # Tabla de interceptación: action_name → callable(HVContext) → ActionResult
        # Se construye una única vez en set_delegated_actions().
        self._delegated: dict[str, callable] = {}

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
        """
        Construye la tabla de interceptación a partir de los nombres
        recibidos del Gestor en el momento del registro.

        Para cada nombre busca la función correspondiente en api_acciones.py
        (misma fuente de verdad que usa el Gestor para resolver la lista).
        Nombres no reconocidos localmente se ignoran con un warning.

        Se llama una única vez desde register_with_gestor().
        """
        if not action_names:
            logger.info("HV %s: sin acciones delegadas.", self.hypervisor_id)
            return

        try:
            from Gestores.Mundo.api_acciones import ACCIONES
        except ImportError as exc:
            logger.error(
                "No se pudo importar api_acciones para resolver acciones "
                "delegadas: %s. El HV no interceptará ninguna acción.",
                exc,
            )
            return

        tabla: dict[str, callable] = {}
        for name in action_names:
            entry = ACCIONES.get(name)
            if entry is None:
                logger.warning(
                    "Acción delegada '%s' no encontrada en ACCIONES; ignorada.", name
                )
                continue
            fn = entry.get("funcion")
            if fn is None:
                logger.warning(
                    "Acción delegada '%s' no tiene 'funcion' en ACCIONES; ignorada.",
                    name,
                )
                continue
            tabla[name] = fn

        self._delegated = tabla
        logger.info(
            "HV %s: tabla de interceptación construida → %s",
            self.hypervisor_id,
            list(tabla.keys()),
        )

    def is_delegated(self, action_name: str) -> bool:
        """True si la acción se ejecuta localmente en este HV."""
        return action_name in self._delegated

    def execute_delegated(
        self,
        bot_id: str,
        action_name: str,
        payload: bytes,
    ) -> ActionResult:
        """
        Ejecuta una acción delegada localmente.

        Construye un HVContext con el estado actual del bot y llama
        a la función registrada en la tabla de interceptación.

        El world_proxy_servicer llama a este método DESPUÉS de haber
        descontado los puntos con try_spend_points(), igual que haría
        antes de llamar a forward_to_gestor().

        Devuelve ActionResult. Si la función lanza una excepción,
        devuelve ActionResult(ok=False) sin propagar.
        """
        fn = self._delegated.get(action_name)
        if fn is None:
            return ActionResult(
                ok=False,
                error=f"Acción '{action_name}' no está delegada en este HV.",
            )

        with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                return ActionResult(ok=False, error=f"Bot {bot_id!r} no encontrado.")

        ctx = HVContext(bot_id=bot_id, bot_record=rec, payload=payload)

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
        Llama a RegisterHypervisor en el Gestor y, si tiene éxito,
        construye la tabla de interceptación con la lista recibida.

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

    def spawn_bot(self, config: dict) -> BotInfo:
        bot_id = config.get("bot_id", "")
        codigo_gz = config.get("codigo_gz", b"")
        budget = int(config.get("budget", DEFAULT_BUDGET))

        if not bot_id:
            return BotInfo(
                bot_id="",
                hypervisor_id=self.hypervisor_id,
                ok=False,
                error="bot_id vacío",
            )

        codigo_path = self._codigo_path(bot_id)
        try:
            codigo_path.parent.mkdir(parents=True, exist_ok=True)
            codigo_path.write_bytes(gzip.decompress(codigo_gz))
        except Exception as exc:
            logger.error("Error escribiendo código de bot %s: %s", bot_id, exc)
            return BotInfo(
                bot_id=bot_id,
                hypervisor_id=self.hypervisor_id,
                ok=False,
                error=f"Error descomprimiendo código: {exc}",
            )

        with self._lock:
            if len(self._bots) >= self.capacity:
                codigo_path.unlink(missing_ok=True)
                return BotInfo(
                    bot_id=bot_id,
                    hypervisor_id=self.hypervisor_id,
                    ok=False,
                    error="Hypervisor a plena capacidad",
                )
            if bot_id in self._bots:
                logger.warning("spawn_bot: bot %s ya existe; sobreescribiendo.", bot_id)
            self._bots[bot_id] = BotRecord(
                bot_id=bot_id, budget=budget, max_budget=budget
            )

        logger.info("Bot %s spawneado (budget=%d).", bot_id, budget)
        return BotInfo(bot_id=bot_id, hypervisor_id=self.hypervisor_id, ok=True)

    def _codigo_path(self, bot_id: str) -> Path:
        return Path("bots_codigo") / self.hypervisor_id / f"{bot_id}.py"

    def kill_bot(self, bot_id: str) -> None:
        with self._lock:
            if bot_id not in self._bots:
                logger.warning("kill_bot: bot desconocido %s", bot_id)
                return
            del self._bots[bot_id]
        try:
            self._codigo_path(bot_id).unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("No se pudo eliminar código de %s: %s", bot_id, exc)
        logger.info("Bot %s eliminado.", bot_id)

    def get_bot_stats(self, bot_id: str) -> Optional[BotStats]:
        with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                return None
            return BotStats(
                bot_id=bot_id,
                hypervisor_id=self.hypervisor_id,
                points_left=rec.budget,
                alive=rec.alive,
                uptime_s=time.time() - rec.spawned_at,
            )

    def get_bot_status(self, bot_id: str) -> Optional[BotStatus]:
        with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                return None
            return BotStatus(bot_id=bot_id, alive=rec.alive, budget=rec.budget)

    def list_bots(self) -> BotList:
        with self._lock:
            now = time.time()
            return BotList(
                bots=[
                    BotStats(
                        bot_id=rec.bot_id,
                        hypervisor_id=self.hypervisor_id,
                        points_left=rec.budget,
                        alive=rec.alive,
                        uptime_s=now - rec.spawned_at,
                    )
                    for rec in self._bots.values()
                ]
            )

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
            rec.last_action = time.time()
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
                new_pts = new_budgets.get(bot_id, rec.max_budget)
                rec.budget = rec.max_budget = new_pts
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

    def deserialize_entities(self, action_result) -> list[Entity]:
        if not action_result or not action_result.payload:
            return []
        try:
            logger.debug(
                "deserialize_entities: payload de %d bytes (stub).",
                len(action_result.payload),
            )
            return []
        except Exception as exc:
            logger.error("Error deserializando entidades: %s", exc)
            return []

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

    def guardar_estado(self): ...
    def cargar_estado(self): ...
