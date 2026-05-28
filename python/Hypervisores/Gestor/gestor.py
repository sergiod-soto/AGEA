"""
gestor.py — Lógica pura del Gestor de Hypervisores.

No contiene nada de gRPC. Recibe y devuelve tipos Python.
El gestor_servicer.py traduce entre protobuf ↔ estos métodos.

Responsabilidades:
  - Registro y seguimiento de Hypervisores (id, dirección, carga).
  - Registro y seguimiento de Bots (id, hypervisor asignado, fitness).
  - Balanceo de carga al hacer spawn_bot.
  - Reenvío de acciones al Mundo (a través del mundo_client inyectado).
  - Difusión de presupuestos a todos los Hypervisores.
"""

from __future__ import annotations

import logging
import math
import threading
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tipos de retorno internos (simples dataclasses, sin protobuf)
# ---------------------------------------------------------------------------

@dataclass
class BotInfo:
    bot_id: str
    hypervisor_id: str
    proxy_address: str   # dirección host:puerto del Hypervisor al que debe conectarse el bot
    ok: bool = True
    error: str = ""


@dataclass
class BotStats:
    bot_id: str
    fitness: float
    tick: int
    hypervisor_id: str


@dataclass
class BotList:
    bots: list[BotStats]


@dataclass
class FitnessReport:
    entries: list[BotStats]   # todos los bots ordenados por fitness desc


@dataclass
class HypervisorInfo:
    hypervisor_id: str
    address: str
    port: int
    proxy_port: int          # puerto que escucha world_proxy (bots se conectan aquí)
    capacity: int            # slots declarados por el HV (informativo)
    current_load: int = 0    # bots activos ahora mismo
    online: bool = True


@dataclass
class HypervisorList:
    hypervisors: list[HypervisorInfo]


@dataclass
class ActionResult:
    ok: bool
    payload: bytes = b""     # protobuf serializado que devuelve el Mundo
    error: str = ""


# ---------------------------------------------------------------------------
# Gestor
# ---------------------------------------------------------------------------

class Gestor:
    """
    Hub central del sistema evolutivo.

    Parámetros de construcción
    --------------------------
    mundo_client : objeto con método forward_action(bot_id, action_type, payload) → ActionResult
        Puede ser None durante las pruebas; en producción es una instancia de
        MundoClient (que se escribirá en otro fichero).

    bots_por_hypervisor : int
        Único punto de control de capacidad. Determina cuántos bots puede
        alojar cada Hypervisor según el Gestor, independientemente de lo que
        el HV declare en su campo capacity. Si un HV declara un valor distinto
        se emite un warning pero el límite efectivo siempre es este parámetro.
    """

    def __init__(self, mundo_client=None, bots_por_hypervisor: int = 100):
        if bots_por_hypervisor <= 0:
            raise ValueError(
                f"bots_por_hypervisor debe ser > 0, recibido: {bots_por_hypervisor}"
            )

        self.bots_por_hypervisor = bots_por_hypervisor

        self._lock = threading.Lock()

        # hypervisor_id → HypervisorInfo
        self._hypervisors: dict[str, HypervisorInfo] = {}

        # hypervisor_id → cliente gRPC hacia ese hypervisor
        # Se puebla externamente (desde gestor_servicer) cuando un HV se registra.
        self._hypervisor_clients: dict[str, object] = {}

        # bot_id → BotStats
        self._bots: dict[str, BotStats] = {}

        # Contador incremental para next_bot_id(); protegido por _lock
        self._bot_counter: int = 0

        # Cliente hacia el Mundo real (inyectado; puede ser None en tests)
        self.mundo_client = mundo_client

        logger.info(
            "Gestor inicializado (bots_por_hypervisor=%d).", bots_por_hypervisor
        )

    # ------------------------------------------------------------------
    # Capacidad
    # ------------------------------------------------------------------

    def hvs_necesarios(self, total_bots: int) -> int:
        """Calcula cuántos Hypervisores hacen falta para alojar total_bots."""
        return math.ceil(total_bots / self.bots_por_hypervisor)

    def capacidad_total(self) -> int:
        """Slots totales disponibles según los HVs registrados y bots_por_hypervisor."""
        with self._lock:
            return len(self._hypervisors) * self.bots_por_hypervisor

    def next_bot_id(self) -> str:
        """Genera el siguiente ID de bot incremental y thread-safe (bot_0001, bot_0002…)."""
        with self._lock:
            self._bot_counter += 1
            return f"bot_{self._bot_counter:04d}"

    # ------------------------------------------------------------------
    # Registro de Hypervisores
    # ------------------------------------------------------------------

    def register_hypervisor(
        self,
        hypervisor_id: str,
        address: str,
        port: int,
        proxy_port: int,
        capacity: int,
    ) -> None:
        """
        Llamado por un Hypervisor cuando arranca.
        Almacena sus metadatos para poder asignarle bots y llamarle más tarde.

        Si capacity difiere de bots_por_hypervisor se emite un warning: el límite
        efectivo siempre es bots_por_hypervisor, no el valor declarado por el HV.
        """
        if capacity != self.bots_por_hypervisor:
            logger.warning(
                "Hypervisor %s declara capacity=%d pero bots_por_hypervisor=%d; "
                "se usará bots_por_hypervisor como límite efectivo.",
                hypervisor_id, capacity, self.bots_por_hypervisor,
            )

        with self._lock:
            if hypervisor_id in self._hypervisors:
                logger.warning("Hypervisor %s ya registrado; actualizando.", hypervisor_id)

            self._hypervisors[hypervisor_id] = HypervisorInfo(
                hypervisor_id=hypervisor_id,
                address=address,
                port=port,
                proxy_port=proxy_port,
                capacity=capacity,
            )
            logger.info(
                "Hypervisor registrado: %s en %s:%d (proxy:%d, cap_declarada:%d, límite_efectivo:%d)",
                hypervisor_id, address, port, proxy_port, capacity, self.bots_por_hypervisor,
            )

    def set_hypervisor_client(self, hypervisor_id: str, client) -> None:
        """
        Guarda el cliente gRPC hacia un Hypervisor.
        Lo llama el gestor_servicer justo después de register_hypervisor.
        """
        with self._lock:
            self._hypervisor_clients[hypervisor_id] = client

    def update_hypervisor_load(self, hypervisor_id: str, current_load: int) -> None:
        """El Hypervisor nos informa de cuántos bots tiene ahora mismo."""
        with self._lock:
            hv = self._hypervisors.get(hypervisor_id)
            if hv is None:
                logger.warning("update_load de HV desconocido: %s", hypervisor_id)
                return
            hv.current_load = current_load
            logger.debug("HV %s carga actualizada a %d.", hypervisor_id, current_load)

    def list_hypervisors(self) -> HypervisorList:
        with self._lock:
            return HypervisorList(hypervisors=list(self._hypervisors.values()))

    # ------------------------------------------------------------------
    # Gestión de Bots
    # ------------------------------------------------------------------

    def spawn_bot(self, bot_config: dict) -> BotInfo:
        """
        Asigna un bot al Hypervisor con más capacidad libre y le ordena crearlo.

        bot_config espera al menos:
          - "bot_id": str  (identificador único del bot)
          - cualquier otro campo de configuración genética

        Devuelve BotInfo con la dirección proxy a la que el bot debe conectarse.
        """
        bot_id = bot_config.get("bot_id", "")
        if not bot_id:
            return BotInfo(bot_id="", hypervisor_id="", proxy_address="", ok=False,
                           error="bot_id vacío")

        with self._lock:
            hv = self._select_hypervisor()
            if hv is None:
                return BotInfo(bot_id=bot_id, hypervisor_id="", proxy_address="",
                               ok=False, error="Sin Hypervisores disponibles")

            # Reservamos el slot optimistamente; el HV puede rechazarlo si está lleno
            hv.current_load += 1

            # Registramos el bot localmente
            self._bots[bot_id] = BotStats(
                bot_id=bot_id,
                fitness=0.0,
                tick=0,
                hypervisor_id=hv.hypervisor_id,
            )

        # Llamamos al Hypervisor para que haga el spawn real
        client = self._hypervisor_clients.get(hv.hypervisor_id)
        if client is None:
            logger.error("No hay cliente para HV %s", hv.hypervisor_id)
            with self._lock:
                hv.current_load -= 1
                del self._bots[bot_id]
            return BotInfo(bot_id=bot_id, hypervisor_id="", proxy_address="",
                           ok=False, error=f"Sin cliente para {hv.hypervisor_id}")

        try:
            result = client.spawn_bot(bot_config)   # devuelve BotInfo
        except Exception as exc:
            logger.error("Error spawn_bot en HV %s: %s", hv.hypervisor_id, exc)
            with self._lock:
                hv.current_load -= 1
                del self._bots[bot_id]
            return BotInfo(bot_id=bot_id, hypervisor_id="", proxy_address="",
                           ok=False, error=str(exc))

        logger.info("Bot %s spawneado en HV %s", bot_id, hv.hypervisor_id)
        return BotInfo(
            bot_id=bot_id,
            hypervisor_id=hv.hypervisor_id,
            proxy_address=f"{hv.address}:{hv.proxy_port}",
            ok=result.ok,
            error=result.error,
        )

    def kill_bot(self, bot_id: str) -> None:
        """Mata un bot en su Hypervisor y lo elimina del registro."""
        with self._lock:
            stats = self._bots.get(bot_id)
            if stats is None:
                logger.warning("kill_bot: bot desconocido %s", bot_id)
                return
            hv_id = stats.hypervisor_id

        client = self._hypervisor_clients.get(hv_id)
        if client:
            try:
                client.kill_bot(bot_id)
            except Exception as exc:
                logger.error("Error kill_bot en HV %s: %s", hv_id, exc)

        with self._lock:
            self._bots.pop(bot_id, None)
            hv = self._hypervisors.get(hv_id)
            if hv and hv.current_load > 0:
                hv.current_load -= 1

        logger.info("Bot %s eliminado.", bot_id)

    # ------------------------------------------------------------------
    # Fitness
    # ------------------------------------------------------------------

    def update_fitness(self, bot_id: str, fitness: float, tick: int) -> None:
        """El Mundo nos informa del fitness de un bot tras evaluar su acción."""
        with self._lock:
            stats = self._bots.get(bot_id)
            if stats is None:
                # El bot puede haber muerto justo antes; ignoramos silenciosamente
                return
            stats.fitness = fitness
            stats.tick = tick

    def build_fitness_report(self) -> FitnessReport:
        """Devuelve todos los bots ordenados por fitness descendente."""
        with self._lock:
            sorted_bots = sorted(self._bots.values(),
                                 key=lambda b: b.fitness, reverse=True)
            return FitnessReport(entries=list(sorted_bots))

    # ------------------------------------------------------------------
    # Acciones → Mundo
    # ------------------------------------------------------------------

    def forward_action_to_mundo(
        self,
        bot_id: str,
        hypervisor_id: str,
        action_type: str,
        payload: bytes,
    ) -> ActionResult:
        """
        El Hypervisor sube aquí las acciones de un bot para que el Gestor
        las reenvíe al Mundo real.

        Si mundo_client es None (tests), devuelve un ActionResult vacío con ok=True.
        """
        if self.mundo_client is None:
            logger.debug("forward_action: sin mundo_client, devolviendo stub.")
            return ActionResult(ok=True, payload=b"")

        try:
            result = self.mundo_client.forward_action(bot_id, action_type, payload)
            return result
        except Exception as exc:
            logger.error("Error forwarding action al Mundo: %s", exc)
            return ActionResult(ok=False, error=str(exc))

    # ------------------------------------------------------------------
    # Presupuestos
    # ------------------------------------------------------------------

    def broadcast_budgets(
        self,
        default_budget: int,
        overrides: dict[str, int] | None = None,
    ) -> None:
        """
        Llama a reset_budgets en todos los Hypervisores online.

        overrides: {bot_id: presupuesto_especial}
        Si un bot no está en overrides, recibe default_budget.
        """
        overrides = overrides or {}

        with self._lock:
            hvs = list(self._hypervisors.values())
            bots_snapshot = dict(self._bots)

        for hv in hvs:
            if not hv.online:
                continue

            # Bots de este HV
            bot_ids = [b.bot_id for b in bots_snapshot.values()
                       if b.hypervisor_id == hv.hypervisor_id]
            if not bot_ids:
                continue

            client = self._hypervisor_clients.get(hv.hypervisor_id)
            if client is None:
                logger.warning("broadcast_budgets: sin cliente para %s", hv.hypervisor_id)
                continue

            # Construimos el mapa de presupuesto individual para este HV
            budget_map = {bid: overrides.get(bid, default_budget) for bid in bot_ids}

            try:
                client.reset_budgets(bot_ids, budget_map)
                logger.debug("Presupuestos enviados a HV %s: %s", hv.hypervisor_id, budget_map)
            except Exception as exc:
                logger.error("Error reset_budgets en HV %s: %s", hv.hypervisor_id, exc)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _select_hypervisor(self) -> Optional[HypervisorInfo]:
        """
        Devuelve el Hypervisor online con más slots libres.

        El límite efectivo es self.bots_por_hypervisor (no hv.capacity,
        que es meramente informativo).

        Debe llamarse con self._lock ya adquirido.
        """
        candidates = [
            hv for hv in self._hypervisors.values()
            if hv.online and hv.current_load < self.bots_por_hypervisor
        ]
        if not candidates:
            return None
        # Mayor capacidad libre según el límite central
        return max(candidates, key=lambda hv: self.bots_por_hypervisor - hv.current_load)
