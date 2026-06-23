"""
gestor_bots.py — Lógica pura del Gestor de Hypervisores.

No contiene nada de gRPC. Recibe y devuelve tipos Python.
El gestor_bots_servicer.py traduce entre protobuf ↔ estos métodos.

Responsabilidades:
  - Registro y seguimiento de Hypervisores (id, dirección, carga).
  - Registro y seguimiento de Bots (id, hypervisor asignado, fitness).
  - Balanceo de carga al hacer spawn_bot.
  - Reenvío de acciones al Mundo (a través del mundo_client inyectado).
  - Difusión de presupuestos a todos los Hypervisores.
  - Resolución de qué acciones delega cada HV (una vez al registrarse).
"""

from __future__ import annotations

import logging
import math
import threading
from dataclasses import dataclass
from typing import Optional

from Gestores.Bots.Hypervisor.hypervisor import BotStats
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import ActionResult
from Gestores.Transporte.gestor_bots_client import BotInfo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tipos de retorno internos
# ---------------------------------------------------------------------------


@dataclass
class HypervisorInfo:
    hypervisor_id: str
    address: str
    port: int
    proxy_port: int
    capacity: int
    current_load: int = 0
    online: bool = True


@dataclass
class HypervisorList:
    hypervisors: list[HypervisorInfo]


# ---------------------------------------------------------------------------
# Gestor_Bots
# ---------------------------------------------------------------------------


class Gestor_Bots:
    """
    Hub central del sistema evolutivo.

    Parámetros
    ----------
    mundo_client : objeto con método forward_action(bot_id, action_type, payload)
    bots_por_hypervisor : int
        Único punto de control de capacidad por HV.
    """

    def __init__(self, mundo_client=None, bots_por_hypervisor: int = 100):
        if bots_por_hypervisor <= 0:
            raise ValueError(
                f"bots_por_hypervisor debe ser > 0, recibido: {bots_por_hypervisor}"
            )

        self.bots_por_hypervisor = bots_por_hypervisor
        self._lock = threading.Lock()
        self._hypervisors: dict[str, HypervisorInfo] = {}
        self._hypervisor_clients: dict[str, object] = {}
        self._bots: dict[str, BotStats] = {}
        self._bot_counter: int = 0
        self.mundo_client = mundo_client

        # Cache de nombres delegados — se calcula una vez en el primer uso
        self._delegated_names_cache: list[str] | None = None

        logger.info(
            "Gestor_Bots inicializado (bots_por_hypervisor=%d).", bots_por_hypervisor
        )

    # ------------------------------------------------------------------
    # Acciones delegadas a HVs
    # ------------------------------------------------------------------

    def get_delegated_action_names(self) -> list[str]:
        """
        Devuelve los nombres de las acciones que los Hypervisores deben
        interceptar y ejecutar localmente en lugar de reenviar al Mundo.

        Lee acciones_delegadas.py (registro estático) y resuelve los nombres
        consultando ACCIONES en api_acciones.py.

        El resultado se cachea: el fichero no cambia en tiempo de ejecución.
        Se llama una vez por HV en el momento de su registro.
        """
        if self._delegated_names_cache is not None:
            return self._delegated_names_cache

        try:
            from Gestores.Bots.Gestor_Bots.acciones_delegadas import ACCIONES_DELEGADAS
            from Gestores.Mundo.api_acciones import ACCIONES

            # Mapa inverso: callable → nombre de acción
            funcion_to_name = {v["funcion"]: k for k, v in ACCIONES.items()}

            nombres = [
                funcion_to_name[fn]
                for fn in ACCIONES_DELEGADAS
                if fn in funcion_to_name
            ]

            logger.info("Acciones delegadas a HVs: %s", nombres)
            self._delegated_names_cache = nombres

        except Exception as exc:
            logger.error(
                "Error resolviendo acciones delegadas: %s. "
                "Los HVs no interceptarán ninguna acción.",
                exc,
            )
            self._delegated_names_cache = []

        return self._delegated_names_cache

    # ------------------------------------------------------------------
    # Capacidad
    # ------------------------------------------------------------------

    def hvs_necesarios(self, total_bots: int) -> int:
        return math.ceil(total_bots / self.bots_por_hypervisor)

    def capacidad_total(self) -> int:
        with self._lock:
            return len(self._hypervisors) * self.bots_por_hypervisor

    def next_bot_id(self) -> str:
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
        if capacity != self.bots_por_hypervisor:
            logger.warning(
                "HV %s declara capacity=%d pero bots_por_hypervisor=%d; "
                "se usará bots_por_hypervisor como límite efectivo.",
                hypervisor_id,
                capacity,
                self.bots_por_hypervisor,
            )

        with self._lock:
            if hypervisor_id in self._hypervisors:
                logger.warning(
                    "Hypervisor %s ya registrado; actualizando.", hypervisor_id
                )

            self._hypervisors[hypervisor_id] = HypervisorInfo(
                hypervisor_id=hypervisor_id,
                address=address,
                port=port,
                proxy_port=proxy_port,
                capacity=capacity,
            )
            logger.info(
                "Hypervisor registrado: %s en %s:%d (proxy:%d, cap:%d)",
                hypervisor_id,
                address,
                port,
                proxy_port,
                capacity,
            )

    def set_hypervisor_client(self, hypervisor_id: str, client) -> None:
        with self._lock:
            self._hypervisor_clients[hypervisor_id] = client

    def update_hypervisor_load(self, hypervisor_id: str, current_load: int) -> None:
        with self._lock:
            hv = self._hypervisors.get(hypervisor_id)
            if hv is None:
                logger.warning("update_load de HV desconocido: %s", hypervisor_id)
                return
            hv.current_load = current_load

    def list_hypervisors(self) -> HypervisorList:
        with self._lock:
            return HypervisorList(hypervisors=list(self._hypervisors.values()))

    # ------------------------------------------------------------------
    # Gestión de Bots
    # ------------------------------------------------------------------

    def spawn_bot(self, bot_config: dict) -> BotInfo:

        bot_id = bot_config.get("bot_id", "")

        if not bot_id:
            return BotInfo(
                bot_id="",
                hypervisor_id="",
                proxy_address="",
                ok=False,
                error="bot_id vacío",
            )

        with self._lock:
            hv = self._select_hypervisor()
            if hv is None:
                return BotInfo(
                    bot_id=bot_id,
                    hypervisor_id="",
                    proxy_address="",
                    ok=False,
                    error="Sin Hypervisores disponibles",
                )
            hv.current_load += 1
            self._bots[bot_id] = BotStats(
                bot_id=bot_id,
                hypervisor_id=hv.hypervisor_id,
                points_left=bot_config.get("budget", 0),
                alive=True,
                uptime_s=0.0,
            )

        client = self._hypervisor_clients.get(hv.hypervisor_id)
        if client is None:
            logger.error("No hay cliente para HV %s", hv.hypervisor_id)
            with self._lock:
                hv.current_load -= 1
                del self._bots[bot_id]
            return BotInfo(
                bot_id=bot_id,
                hypervisor_id="",
                proxy_address="",
                ok=False,
                error=f"Sin cliente para {hv.hypervisor_id}",
            )

        try:
            result = client.spawn_bot(bot_config)
        except Exception as exc:
            logger.error("Error spawn_bot en HV %s: %s", hv.hypervisor_id, exc)
            with self._lock:
                hv.current_load -= 1
                del self._bots[bot_id]
            return BotInfo(
                bot_id=bot_id,
                hypervisor_id="",
                proxy_address="",
                ok=False,
                error=str(exc),
            )

        return BotInfo(
            bot_id=bot_id,
            hypervisor_id=hv.hypervisor_id,
            proxy_address=f"{hv.address}:{hv.proxy_port}",
            ok=result.ok,
            error=result.error,
        )

    def kill_bot(self, bot_id: str) -> None:
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
        if self.mundo_client is None:
            logger.debug("forward_action: sin mundo_client, devolviendo stub.")
            return ActionResult(ok=True, payload=b"")

        try:
            return self.mundo_client.forward_action(bot_id, action_type, payload)
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
        overrides = overrides or {}

        with self._lock:
            hvs = list(self._hypervisors.values())
            bots_snapshot = dict(self._bots)

        for hv in hvs:
            if not hv.online:
                continue
            bot_ids = [
                b.bot_id
                for b in bots_snapshot.values()
                if b.hypervisor_id == hv.hypervisor_id
            ]
            if not bot_ids:
                continue
            client = self._hypervisor_clients.get(hv.hypervisor_id)
            if client is None:
                logger.warning(
                    "broadcast_budgets: sin cliente para %s", hv.hypervisor_id
                )
                continue
            budget_map = {bid: overrides.get(bid, default_budget) for bid in bot_ids}
            try:
                client.reset_budgets(bot_ids, budget_map)
            except Exception as exc:
                logger.error("Error reset_budgets en HV %s: %s", hv.hypervisor_id, exc)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _select_hypervisor(self) -> Optional[HypervisorInfo]:
        """Debe llamarse con self._lock adquirido."""
        candidates = [
            hv
            for hv in self._hypervisors.values()
            if hv.online and hv.current_load < self.bots_por_hypervisor
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda hv: hv.current_load)
