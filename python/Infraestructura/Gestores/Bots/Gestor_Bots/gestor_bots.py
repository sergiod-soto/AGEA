"""
gestor_bots.py — Lógica pura del Gestor de Hypervisores.
"""

from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass
from typing import Optional

from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import BotInfo, BotStats
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import ActionResult

logger = logging.getLogger(__name__)


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


class Gestor_Bots:

    def __init__(self, mundo_client=None, bots_por_hypervisor: int = 100):
        if bots_por_hypervisor <= 0:
            raise ValueError(
                f"bots_por_hypervisor debe ser > 0, recibido: {bots_por_hypervisor}"
            )

        self.bots_por_hypervisor = bots_por_hypervisor
        self._lock = asyncio.Lock()
        self._hypervisors: dict[str, HypervisorInfo] = {}
        self._hypervisor_clients: dict[str, object] = {}
        self._bots: dict[str, BotStats] = {}
        self._bot_counter: int = 0
        self.mundo_client = mundo_client
        self._delegated_names_cache: list[str] | None = None

        logger.info(
            "Gestor_Bots inicializado (bots_por_hypervisor=%d).", bots_por_hypervisor
        )

    # ------------------------------------------------------------------
    # Acciones delegadas
    # ------------------------------------------------------------------

    def get_delegated_action_names(self) -> list[str]:
        if self._delegated_names_cache is not None:
            return self._delegated_names_cache

        try:
            from Infraestructura.Gestores.Bots.Gestor_Bots.acciones_delegadas import ACCIONES_DELEGADAS
            from Infraestructura.Gestores.Mundo.Logica_Mundo.api_acciones import ACCIONES

            nombres = [name for name in ACCIONES_DELEGADAS if name in ACCIONES]
            nombres_invalidos = set(ACCIONES_DELEGADAS) - set(nombres)
            if nombres_invalidos:
                logger.warning(
                    "Acciones delegadas no encontradas en ACCIONES: %s",
                    nombres_invalidos,
                )

            logger.info("Acciones delegadas a HVs: %s", nombres)
            self._delegated_names_cache = nombres

        except Exception as exc:
            logger.error("Error resolviendo acciones delegadas: %s.", exc)
            self._delegated_names_cache = []

        return self._delegated_names_cache

    # ------------------------------------------------------------------
    # Capacidad
    # ------------------------------------------------------------------

    def hvs_necesarios(self, total_bots: int) -> int:
        return math.ceil(total_bots / self.bots_por_hypervisor)

    async def capacidad_total(self) -> int:
        async with self._lock:
            return len(self._hypervisors) * self.bots_por_hypervisor

    async def next_bot_id(self) -> str:
        async with self._lock:
            self._bot_counter += 1
            return f"bot_{self._bot_counter:04d}"

    # ------------------------------------------------------------------
    # Registro de Hypervisores
    # ------------------------------------------------------------------

    async def register_hypervisor(
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

        async with self._lock:
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

    async def set_hypervisor_client(self, hypervisor_id: str, client) -> None:
        async with self._lock:
            self._hypervisor_clients[hypervisor_id] = client

    async def update_hypervisor_load(
        self, hypervisor_id: str, current_load: int
    ) -> None:
        async with self._lock:
            hv = self._hypervisors.get(hypervisor_id)
            if hv is None:
                logger.warning("update_load de HV desconocido: %s", hypervisor_id)
                return
            hv.current_load = current_load

    async def list_hypervisors(self) -> HypervisorList:
        async with self._lock:
            return HypervisorList(hypervisors=list(self._hypervisors.values()))

    # ------------------------------------------------------------------
    # Gestión de Bots
    # ------------------------------------------------------------------

    async def spawn_bot(self, bot_config: dict) -> BotInfo:
        bot_id = bot_config.get("bot_id", "")

        if not bot_id:
            return BotInfo(
                bot_id="",
                hypervisor_id="",
                proxy_address="",
                ok=False,
                error="bot_id vacío",
            )

        async with self._lock:
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
            hv_id = hv.hypervisor_id
            proxy_address = f"{hv.address}:{hv.proxy_port}"

        if client is None:
            logger.error("No hay cliente para HV %s", hv_id)
            async with self._lock:
                hv = self._hypervisors.get(hv_id)
                if hv:
                    hv.current_load -= 1
                self._bots.pop(bot_id, None)
            return BotInfo(
                bot_id=bot_id,
                hypervisor_id="",
                proxy_address="",
                ok=False,
                error=f"Sin cliente para {hv_id}",
            )

        try:
            result = await client.spawn_bot(bot_config)
        except Exception as exc:
            logger.error("Error spawn_bot en HV %s: %s", hv_id, exc)
            async with self._lock:
                hv = self._hypervisors.get(hv_id)
                if hv:
                    hv.current_load -= 1
                self._bots.pop(bot_id, None)
            return BotInfo(
                bot_id=bot_id,
                hypervisor_id="",
                proxy_address="",
                ok=False,
                error=str(exc),
            )

        return BotInfo(
            bot_id=bot_id,
            hypervisor_id=hv_id,
            proxy_address=proxy_address,
            ok=result.ok,
            error=result.error,
        )

    async def kill_bot(self, bot_id: str) -> None:
        async with self._lock:
            stats = self._bots.get(bot_id)
            if stats is None:
                logger.warning("kill_bot: bot desconocido %s", bot_id)
                return
            hv_id = stats.hypervisor_id
            client = self._hypervisor_clients.get(hv_id)

        if client:
            try:
                await client.kill_bot(bot_id)
            except Exception as exc:
                logger.error("Error kill_bot en HV %s: %s", hv_id, exc)

        async with self._lock:
            self._bots.pop(bot_id, None)
            hv = self._hypervisors.get(hv_id)
            if hv and hv.current_load > 0:
                hv.current_load -= 1

    async def notify_bot_death_async(self, bot_id: str, cause: str, tick: int) -> None:
        async with self._lock:
            stats = self._bots.pop(bot_id, None)
            if stats is not None:
                hv = self._hypervisors.get(stats.hypervisor_id)
                if hv and hv.current_load > 0:
                    hv.current_load -= 1

        if self.mundo_client is not None:
            try:
                await self.mundo_client.notify_bot_death(bot_id, cause, tick)
            except Exception as exc:
                logger.error(
                    "Error notificando muerte de bot %s al Mundo: %s", bot_id, exc
                )

    # ------------------------------------------------------------------
    # Acciones → Mundo
    # ------------------------------------------------------------------

    async def forward_action_to_mundo(
        self,
        bot_id: str,
        hypervisor_id: str,
        action_type: str,
        payload: bytes,
    ) -> ActionResult:
        if self.mundo_client is None:
            return ActionResult(ok=True, payload=b"", error="")
        try:
            return await self.mundo_client.forward_action(bot_id, action_type, payload)
        except Exception as exc:
            logger.error("Error forwarding action al Mundo: %s", exc)
            return ActionResult(ok=False, payload=b"", error=str(exc))

    # ------------------------------------------------------------------
    # Presupuestos
    # ------------------------------------------------------------------

    async def broadcast_budgets_async(
        self,
        default_budget: int,
        overrides: dict[str, int] | None = None,
    ) -> None:
        overrides = overrides or {}
        async with self._lock:
            hvs = list(self._hypervisors.values())
            bots_snapshot = dict(self._bots)
            clients = dict(self._hypervisor_clients)

        tareas = []
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
            client = clients.get(hv.hypervisor_id)
            if client is None:
                logger.warning(
                    "broadcast_budgets: sin cliente para %s", hv.hypervisor_id
                )
                continue
            budget_map = {bid: overrides.get(bid, default_budget) for bid in bot_ids}
            tareas.append(
                self._reset_hv_budgets(client, hv.hypervisor_id, bot_ids, budget_map)
            )

        if tareas:
            await asyncio.gather(*tareas, return_exceptions=True)

    # ------------------------------------------------------------------
    # Freeze / Resume / Snapshot
    # ------------------------------------------------------------------

    async def freeze_all_async(self) -> None:
        async with self._lock:
            clients = list(self._hypervisor_clients.items())

        results = await asyncio.gather(
            *[self._freeze_hv(hv_id, client) for hv_id, client in clients],
            return_exceptions=True,
        )
        for (hv_id, _), result in zip(clients, results):
            if isinstance(result, Exception):
                logger.error("Error freezing HV %s: %s", hv_id, result)

    async def resume_all_async(self) -> None:
        async with self._lock:
            clients = list(self._hypervisor_clients.items())

        await asyncio.gather(
            *[self._resume_hv(hv_id, client) for hv_id, client in clients],
            return_exceptions=True,
        )

    async def save_snapshot_async(self, snapshot_id: str) -> None:
        async with self._lock:
            clients = list(self._hypervisor_clients.items())

        await asyncio.gather(
            *[
                self._save_hv_snapshot(hv_id, client, snapshot_id)
                for hv_id, client in clients
            ],
            return_exceptions=True,
        )

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

    async def _reset_hv_budgets(self, client, hv_id, bot_ids, budget_map) -> None:
        try:
            await client.reset_budgets(bot_ids, budget_map)
        except Exception as exc:
            logger.error("Error reset_budgets en HV %s: %s", hv_id, exc)

    async def _freeze_hv(self, hv_id: str, client) -> None:
        try:
            await client.freeze()
        except Exception as exc:
            logger.error("freeze_hv %s: %s", hv_id, exc)
            raise

    async def _resume_hv(self, hv_id: str, client) -> None:
        try:
            await client.resume()
        except Exception as exc:
            logger.error("resume_hv %s: %s", hv_id, exc)

    async def _save_hv_snapshot(self, hv_id: str, client, snapshot_id: str) -> None:
        try:
            await client.save_snapshot(snapshot_id)
        except Exception as exc:
            logger.error("save_snapshot HV %s: %s", hv_id, exc)
