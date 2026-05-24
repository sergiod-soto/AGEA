"""
hypervisor.py — Lógica pura del Hypervisor.

No contiene nada de gRPC. Recibe y devuelve tipos Python.
Dos servicers lo envuelven:
  - hypervisor_servicer.py   → canal Gestor → Hypervisor
  - world_proxy_servicer.py  → canal Bot    → Hypervisor (proxy al Mundo)

Responsabilidades:
  - Ciclo de vida de bots locales (spawn, kill, stats).
  - Control de presupuesto de puntos por ciclo (try_spend_points).
  - Deserialización de entidades del ActionResult del Mundo.
  - Reenvío de acciones al Gestor (a través del gestor_client inyectado).
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Costes de acción (igual que world_proxy_servicer los necesitará)
# ---------------------------------------------------------------------------

ACTION_COSTS: dict[str, int] = {
    "observe": 1,
    "move": 2,
    "rotate": 2,
    "interact": 3,
}

DEFAULT_BUDGET = 100  # puntos por ciclo si el Gestor no especifica otro


# ---------------------------------------------------------------------------
# Tipos internos
# ---------------------------------------------------------------------------


@dataclass
class BotRecord:
    """Estado local de un bot en este Hypervisor."""

    bot_id: str
    budget: int  # puntos restantes en el ciclo actual
    max_budget: int  # presupuesto máximo (se restaura cada ciclo)
    alive: bool = True
    spawned_at: float = field(default_factory=time.time)
    last_action: float = 0.0  # timestamp de la última acción


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
    uptime_s: float  # segundos desde el spawn


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
    """Entidad del mundo deserializada (espejo de common.proto Entity)."""

    entity_id: str
    type: str  # "bot" | "resource" | "obstacle" | "projectile"
    x: float
    y: float
    rotation: float
    health: float
    attributes: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Hypervisor
# ---------------------------------------------------------------------------


class Hypervisor:
    """
    Proxy transparente entre los Bots y el Mundo.

    Parámetros de construcción
    --------------------------
    hypervisor_id : str
        Identificador único de esta instancia.
    gestor_client : GestorClient
        Cliente ya conectado al Gestor. El Hypervisor lo usa para:
          - Registrarse al arrancar.
          - Subir acciones de bots (ForwardAction).
          - Reportar su carga periódicamente.
    capacity : int
        Número máximo de bots simultáneos.
    my_address : str
        Dirección IP/hostname en la que este Hypervisor es accesible
        (se informa al Gestor al registrarse).
    my_port : int
        Puerto del HypervisorService (canal Gestor → HV).
    my_proxy_port : int
        Puerto del WorldProxyService (canal Bot → HV).
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

        # bot_id → BotRecord
        self._bots: dict[str, BotRecord] = {}

        logger.info(
            "Hypervisor %s inicializado (cap=%d, proxy=%s:%d)",
            hypervisor_id,
            capacity,
            my_address,
            my_proxy_port,
        )

    # ------------------------------------------------------------------
    # Registro en el Gestor
    # ------------------------------------------------------------------

    def register_with_gestor(self) -> bool:
        """
        Llama a RegisterHypervisor en el Gestor.
        Se invoca desde el servidor de arranque justo después de start().
        Devuelve True si el Gestor aceptó el registro.
        """
        ok = self.gestor_client.register_hypervisor(
            hypervisor_id=self.hypervisor_id,
            address=self._my_address,
            port=self._my_port,
            proxy_port=self._my_proxy_port,
            capacity=self.capacity,
        )
        if ok:
            logger.info("Registrado correctamente en el Gestor.")
        else:
            logger.error("El Gestor rechazó el registro.")
        return ok

    def report_load(self) -> None:
        """
        Informa al Gestor de cuántos bots tenemos ahora mismo.
        Se puede llamar periódicamente desde un hilo de heartbeat.
        """
        with self._lock:
            load = len(self._bots)
        self.gestor_client.update_hypervisor_load(self.hypervisor_id, load)

    # ------------------------------------------------------------------
    # Ciclo de vida de bots
    # (llamado desde hypervisor_servicer, que recibe órdenes del Gestor)
    # ------------------------------------------------------------------

    def spawn_bot(self, config: dict) -> BotInfo:
        """
        Crea el registro local de un bot.

        config espera:
          - "bot_id"  : str
          - "budget"  : int  (opcional, default DEFAULT_BUDGET)
        """
        bot_id = config.get("bot_id", "")
        if not bot_id:
            return BotInfo(
                bot_id="",
                hypervisor_id=self.hypervisor_id,
                ok=False,
                error="bot_id vacío",
            )

        budget = int(config.get("budget", DEFAULT_BUDGET))

        with self._lock:
            if len(self._bots) >= self.capacity:
                return BotInfo(
                    bot_id=bot_id,
                    hypervisor_id=self.hypervisor_id,
                    ok=False,
                    error="Hypervisor a plena capacidad",
                )

            if bot_id in self._bots:
                logger.warning("spawn_bot: bot %s ya existe; sobreescribiendo.", bot_id)

            self._bots[bot_id] = BotRecord(
                bot_id=bot_id,
                budget=budget,
                max_budget=budget,
            )

        logger.info("Bot %s spawneado (budget=%d).", bot_id, budget)
        return BotInfo(bot_id=bot_id, hypervisor_id=self.hypervisor_id, ok=True)

    def kill_bot(self, bot_id: str) -> None:
        """Elimina el registro local de un bot."""
        with self._lock:
            if bot_id not in self._bots:
                logger.warning("kill_bot: bot desconocido %s", bot_id)
                return
            del self._bots[bot_id]
        logger.info("Bot %s eliminado.", bot_id)

    def get_bot_stats(self, bot_id: str) -> Optional[BotStats]:
        """Devuelve el estado local del bot o None si no existe."""
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
        """
        Versión ligera de get_bot_stats: solo alive + budget.
        La usa el world_proxy_servicer antes de cada acción.
        """
        with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                return None
            return BotStatus(bot_id=bot_id, alive=rec.alive, budget=rec.budget)

    def list_bots(self) -> BotList:
        """Lista todos los bots activos en este Hypervisor."""
        with self._lock:
            now = time.time()
            stats = [
                BotStats(
                    bot_id=rec.bot_id,
                    hypervisor_id=self.hypervisor_id,
                    points_left=rec.budget,
                    alive=rec.alive,
                    uptime_s=now - rec.spawned_at,
                )
                for rec in self._bots.values()
            ]
        return BotList(bots=stats)

    # ------------------------------------------------------------------
    # Control de presupuesto
    # (el método más crítico del Hypervisor)
    # ------------------------------------------------------------------

    def try_spend_points(self, bot_id: str, cost: int) -> tuple[bool, int]:
        """
        Intenta gastar `cost` puntos del presupuesto del bot.

        Devuelve (éxito, puntos_restantes).

        - Si el bot no existe         → (False, 0)
        - Si no tiene suficientes     → (False, puntos_actuales)
        - Si tiene suficientes        → descuenta y devuelve (True, nuevos_puntos)

        Esta operación es atómica (con lock). El world_proxy_servicer la llama
        ANTES de subir la acción al Gestor; si devuelve False, rechaza sin
        ninguna llamada de red adicional.
        """
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
                "Bot %s gastó %d punto(s). Restantes: %d.",
                bot_id,
                cost,
                rec.budget,
            )
            return True, rec.budget

    def set_point_budget(self, bot_id: str, points: int) -> None:
        """
        Establece el presupuesto de un bot específico.
        Llamado por reset_budgets cuando el Gestor envía overrides individuales.
        """
        with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                logger.warning("set_point_budget: bot desconocido %s", bot_id)
                return
            rec.budget = points
            rec.max_budget = points
        logger.debug("Bot %s presupuesto establecido a %d.", bot_id, points)

    def reset_budgets(
        self,
        bot_ids: list[str],
        new_budgets: dict[str, int],
    ) -> None:
        """
        Resetea los presupuestos al inicio de cada ciclo.

        Llamado por el hypervisor_servicer cuando el Gestor emite
        BroadcastBudgets. Cada bot recibe el presupuesto que le corresponde
        según new_budgets; si no aparece en el dict, mantiene su max_budget.

        bot_ids    : lista de bots que deben resetearse (pueden ser un subconjunto).
        new_budgets: {bot_id: puntos}  — puede incluir overrides individuales.
        """
        with self._lock:
            for bot_id in bot_ids:
                rec = self._bots.get(bot_id)
                if rec is None:
                    continue
                new_pts = new_budgets.get(bot_id, rec.max_budget)
                rec.budget = new_pts
                rec.max_budget = new_pts
                logger.debug("Budget reset bot %s → %d.", bot_id, new_pts)

        logger.info(
            "Budgets reseteados para %d bot(s) en HV %s.",
            len(bot_ids),
            self.hypervisor_id,
        )

    # ------------------------------------------------------------------
    # Proxy al Mundo
    # (llamado desde world_proxy_servicer después de try_spend_points)
    # ------------------------------------------------------------------

    def forward_to_gestor(
        self,
        bot_id: str,
        action_type: str,
        payload: bytes,
    ):
        """
        Reenvía la acción de un bot al Gestor (que la mandará al Mundo).

        Devuelve un ActionResult de gestor_client.
        El world_proxy_servicer convierte ese resultado a protobuf y lo
        devuelve al bot.
        """
        return self.gestor_client.forward_action(
            bot_id=bot_id,
            hypervisor_id=self.hypervisor_id,
            action_type=action_type,
            payload=payload,
        )

    # ------------------------------------------------------------------
    # Deserialización de entidades
    # (el world_proxy_servicer puede usarlo para parsear el payload
    #  del ActionResult antes de devolvérselo al bot, aunque también
    #  puede pasarlo opaco; depende del diseño del Mundo)
    # ------------------------------------------------------------------

    def deserialize_entities(self, action_result) -> list[Entity]:
        """
        Convierte el campo payload de un ActionResult en lista de Entity.

        El formato interno depende de cómo el Mundo serialice las entidades.
        Aquí asumimos que el Mundo devuelve los datos ya en protobuf
        (common.ActionResult.payload contiene bytes de una lista de Entity).

        Si el Mundo usa otro formato (msgpack, json…), solo hay que cambiar
        este método; el resto del sistema no se toca.

        Devuelve lista vacía si el payload está vacío o hay error de parseo.
        """
        if not action_result or not action_result.payload:
            return []

        try:
            from Hypervisores.Transporte.Protobufs import common_pb2

            # Intentamos parsear como repeated Entity dentro de un wrapper.
            # Usamos BotList como contenedor temporal: en la práctica el Mundo
            # podría definir un ObserveResult con repeated Entity; aquí lo
            # dejamos preparado para ese caso.
            #
            # Por ahora lo dejamos como stub que el Mundo completará cuando
            # defina su formato de respuesta de observación.
            logger.debug(
                "deserialize_entities: payload de %d bytes (stub).",
                len(action_result.payload),
            )
            return []

        except Exception as exc:
            logger.error("Error deserializando entidades: %s", exc)
            return []
