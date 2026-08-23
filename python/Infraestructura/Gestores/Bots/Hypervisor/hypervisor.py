# Infraestructura/Gestores/Bots/Hypervisor/hypervisor.py
"""
Migrado a asyncio, para que Hypervisor sea consistente con el resto de
componentes (todos asyncio salvo este, que era el único síncrono).

Cambios de fondo respecto a la versión síncrona:
  - threading.Lock -> asyncio.Lock (todos los métodos que tocan estado
    compartido pasan a ser async).
  - subprocess.Popen -> asyncio.create_subprocess_exec
    (LanzadorProcesosBot.lanzar ahora es async).
  - El hilo daemon _watch_bot_process se sustituye por una asyncio.Task
    que espera `await proceso.wait()` — no bloquea el loop de eventos,
    no necesita un hilo aparte.
  - gestor_client pasa a ser GestorBotsClientAsync (await en todas las
    llamadas), en vez del cliente síncrono.

Limpieza: se retira _codigo_path (método muerto — nunca se llamaba;
duplicaba LanzadorProcesosBot.codigo_path, que es la versión real en uso).
"""

from __future__ import annotations

import asyncio
import datetime
import gzip
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil

from Infraestructura.Gestores.tipos_comunes import (
    ActionResult,
    BotInfo,
    BotList,
    BotStats,
    BotStatusHV,
)

logger = logging.getLogger(__name__)

DEFAULT_BUDGET = 100

SNAPSHOT_MAX = int(os.getenv("SNAPSHOT_MAX", "20"))


@dataclass
class BotRecord:
    bot_id: int
    budget: int
    max_budget: int
    alive: bool = True


@dataclass
class SpawnResult:
    ok: bool
    error: str = ""


class LanzadorProcesosBot:
    """
    Encapsula el despliegue real de un bot: descomprimir su código,
    escribirlo a disco y lanzar el proceso del sistema operativo.

    Se inyecta en Hypervisor en vez de vivir hardcodeado dentro de
    spawn_bot/kill_bot.
    """

    def __init__(self, codigo_dir: Path = Path("bots_codigo")):
        self._codigo_dir = codigo_dir

    def codigo_path(self, hypervisor_id: str, bot_id: int) -> Path:
        return self._codigo_dir / hypervisor_id / f"{bot_id}.py"

    async def lanzar(
        self,
        hypervisor_id: str,
        bot_id: int,
        codigo_gz: bytes,
        env_extra: dict,
    ) -> asyncio.subprocess.Process:
        """
        Descomprime codigo_gz, lo escribe a disco y lanza el proceso.
        Deja que cualquier excepción se propague tal cual — spawn_bot
        decide qué hacer si falla (deshacer el registro del bot, etc.).

        La descompresión + escritura a disco siguen siendo síncronas
        (gzip.decompress, Path.write_bytes): son operaciones cortas de
        un solo uso por bot — el bloqueo puntual del loop se considera
        aceptable aquí, no vale la pena la complejidad de moverlas a un
        executor para un fichero de código de bot, normalmente pequeño.
        """
        codigo_path = self.codigo_path(hypervisor_id, bot_id)
        codigo_path.parent.mkdir(parents=True, exist_ok=True)
        codigo_path.write_bytes(gzip.decompress(codigo_gz))

        return await asyncio.create_subprocess_exec(
            sys.executable,
            str(codigo_path),
            env={**os.environ, **env_extra},
        )

    def limpiar(self, hypervisor_id: str, bot_id: int) -> None:
        """Elimina el fichero de código del bot, si existe. Idempotente."""
        self.codigo_path(hypervisor_id, bot_id).unlink(missing_ok=True)


class Hypervisor:
    """
    Proxy transparente entre los Bots y el Mundo.

    Parámetros
    ----------
    hypervisor_id      : str
    gestor_client      : GestorBotsClientAsync (migrado desde la versión
                         síncrona — ver docstring del módulo)
    capacity           : int
    my_address         : str
    my_port            : int
    my_proxy_port      : int
    """

    def __init__(
        self,
        hypervisor_id: str,
        gestor_client,
        capacity: int = 32,
        my_address: str = "localhost",
        my_port: int = 50052,
        my_proxy_port: int = 50053,
        lanzador_procesos: Optional[LanzadorProcesosBot] = None,
    ):
        self.hypervisor_id = hypervisor_id
        self.gestor_client = gestor_client
        self.capacity = capacity
        self._my_address = my_address
        self._my_port = my_port
        self._my_proxy_port = my_proxy_port

        self._lock = asyncio.Lock()
        self._bots: dict[str, BotRecord] = {}
        self._procesos: dict[str, asyncio.subprocess.Process] = {}
        self._watchers: dict[str, asyncio.Task] = {}

        self._lanzador = lanzador_procesos or LanzadorProcesosBot()

        self._frozen = False

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

    async def register_with_gestor(self) -> bool:
        result = await self.gestor_client.register_hypervisor(
            hypervisor_id=self.hypervisor_id,
            address=self._my_address,
            port=self._my_port,
            proxy_port=self._my_proxy_port,
            capacity=self.capacity,
        )
        if result.ok:
            logger.info("HV %s registrado correctamente.", self.hypervisor_id)
        else:
            logger.error(
                "Gestor rechazó registro de HV %s: %s", self.hypervisor_id, result.error
            )
        return result.ok

    async def report_load(self) -> None:
        async with self._lock:
            load = len(self._bots)
        await self.gestor_client.update_hypervisor_load(self.hypervisor_id, load)

    # ------------------------------------------------------------------
    # Ciclo de vida de bots
    # ------------------------------------------------------------------

    async def spawn_bot(self, config: dict) -> SpawnResult:
        bot_id = config.get("bot_id", "")
        codigo_gz = config.get("codigo_gz", b"")
        budget = int(config.get("budget", DEFAULT_BUDGET))

        if not bot_id:
            return SpawnResult(ok=False, error="bot_id vacío")

        async with self._lock:
            if len(self._bots) >= self.capacity:
                return SpawnResult(ok=False, error="Hypervisor a plena capacidad")
            if bot_id in self._bots:
                return SpawnResult(
                    ok=False, error=f"Bot {bot_id!r} ya existe en este HV"
                )
            self._bots[bot_id] = BotRecord(
                bot_id=bot_id, budget=budget, max_budget=budget, alive=False
            )

        try:
            proceso = await self._lanzador.lanzar(
                hypervisor_id=self.hypervisor_id,
                bot_id=bot_id,
                codigo_gz=codigo_gz,
                env_extra={
                    "BOT_ID": bot_id,
                    "HV_PROXY_ADDRESS": f"{self._my_address}:{self._my_proxy_port}",
                },
            )
        except Exception as exc:
            async with self._lock:
                self._bots.pop(bot_id, None)
            self._lanzador.limpiar(self.hypervisor_id, bot_id)
            logger.error("Error desplegando bot %s: %s", bot_id, exc)
            return SpawnResult(ok=False, error=f"Error desplegando bot: {exc}")

        async with self._lock:
            self._bots[bot_id].alive = True
            self._procesos[bot_id] = proceso

        # Antes: threading.Thread bloqueado en proceso.wait(). Ahora:
        # una Task que espera de forma no bloqueante — no ocupa un hilo,
        # el loop sigue atendiendo el resto de RPCs mientras tanto.
        self._watchers[bot_id] = asyncio.create_task(
            self._watch_bot_process(bot_id, proceso),
            name=f"bot-watcher-{bot_id}",
        )

        logger.info("Bot %s spawneado (budget=%d).", bot_id, budget)
        return SpawnResult(ok=True)

    async def _watch_bot_process(
        self, bot_id: int, proceso: asyncio.subprocess.Process
    ) -> None:
        await proceso.wait()

        async with self._lock:
            crash = bot_id in self._bots
            if crash:
                self._bots.pop(bot_id, None)
                self._procesos.pop(bot_id, None)
            self._watchers.pop(bot_id, None)

        if not crash:
            return

        logger.warning(
            "Bot %s: proceso terminado inesperadamente (código=%s) — "
            "notificando avatar sin piloto.",
            bot_id,
            proceso.returncode,
        )

        try:
            self._lanzador.limpiar(self.hypervisor_id, bot_id)
        except Exception as exc:
            logger.warning(
                "No se pudo eliminar código de %s tras crash: %s", bot_id, exc
            )

        try:
            await self.gestor_client.notificar_avatar_sin_piloto(bot_id)
        except Exception as exc:
            logger.error("Error notificando avatar sin piloto para %s: %s", bot_id, exc)

    async def get_bot_stats(self, bot_id: int) -> Optional[BotStats]:
        async with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                return None
            return BotStats(
                bot_id=rec.bot_id,
                hypervisor_id=self.hypervisor_id,
                points_left=rec.budget,
                alive=rec.alive,
            )

    async def get_bot_status(self, bot_id: int) -> Optional[BotStatusHV]:
        async with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                return None
            return BotStatusHV(bot_id=rec.bot_id, alive=rec.alive, budget=rec.budget)

    async def list_bots(self) -> BotList:
        async with self._lock:
            return BotList(
                bots=[
                    BotStats(
                        bot_id=rec.bot_id,
                        hypervisor_id=self.hypervisor_id,
                        points_left=rec.budget,
                        alive=rec.alive,
                    )
                    for rec in self._bots.values()
                ]
            )

    async def kill_bot(self, bot_id: int) -> None:
        async with self._lock:
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
            self._lanzador.limpiar(self.hypervisor_id, bot_id)
        except Exception as exc:
            logger.warning("No se pudo eliminar código de %s: %s", bot_id, exc)

        logger.info("Bot %s eliminado.", bot_id)

    # ------------------------------------------------------------------
    # Control de presupuesto
    # ------------------------------------------------------------------

    async def try_spend_points(self, bot_id: int, cost: int) -> tuple[bool, int]:
        async with self._lock:
            if self._frozen:
                return False, 0
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
            return True, rec.budget

    async def set_point_budget(self, bot_id: int, points: int) -> None:
        async with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                logger.warning("set_point_budget: bot desconocido %s", bot_id)
                return
            rec.budget = rec.max_budget = points

    async def reset_budgets(
        self, bot_ids: list[str], new_budgets: dict[str, int]
    ) -> None:
        async with self._lock:
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
    # Proxy al Gestor
    # ------------------------------------------------------------------

    async def forward_to_gestor(
        self, bot_id: int, action_type: str, payload: bytes
    ) -> ActionResult:
        """Redirige una acción al gestor_bots (para acciones que pasan por él)."""
        return await self.gestor_client.forward_action(
            bot_id=bot_id,
            hypervisor_id=self.hypervisor_id,
            action_type=action_type,
            payload=payload,
        )

    # ------------------------------------------------------------------
    # Métricas de sistema
    # ------------------------------------------------------------------

    def get_system_load(self) -> dict:
        # Sin cambios: psutil ya es síncrono y rápido (lectura de
        # contadores del sistema) — no aporta nada envolverlo en async.
        def _is_aws() -> bool:
            return "AWS_BATCH_JOB_ID" in os.environ

        mem = psutil.virtual_memory()
        base = {
            "mem_percent": mem.percent,
            "mem_used_mb": round(mem.used / 1024 / 1024, 2),
            "mem_total_mb": round(mem.total / 1024 / 1024, 2),
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

    # ------------------------------------------------------------------
    # Gestion Hypervisores
    # ------------------------------------------------------------------

    async def freeze(self) -> None:
        async with self._lock:
            self._frozen = True
        logger.info("Hypervisor %s congelado.", self.hypervisor_id)

    async def resume(self) -> None:
        async with self._lock:
            self._frozen = False
        logger.info("Hypervisor %s reanudado.", self.hypervisor_id)

    async def save_snapshot(self, snapshot_id: str) -> None:
        async with self._lock:
            bots_snapshot = [
                {
                    "bot_id": rec.bot_id,
                    "budget": rec.budget,
                    "max_budget": rec.max_budget,
                    "alive": rec.alive,
                }
                for rec in self._bots.values()
            ]

        state = {
            "snapshot_id": snapshot_id,
            "hypervisor_id": self.hypervisor_id,
            "fecha": datetime.datetime.now().isoformat(),
            "bots": bots_snapshot,
        }
        path = Path("data/snapshots") / f"{self.hypervisor_id}_{snapshot_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state))
        logger.info("Hypervisor %s snapshot guardado: %s", self.hypervisor_id, path)

        self._purgar_snapshots_antiguos()

    def _purgar_snapshots_antiguos(self) -> None:
        """
        Mantiene como máximo SNAPSHOT_MAX ficheros de snapshot para este
        hypervisor, borrando los más antiguos por número de snapshot (no
        por fecha de disco, para no depender de que el mtime sea fiable).
        Se llama tras cada guardado, así el límite se aplica de forma
        incremental sin picos de borrado masivo.
        """
        carpeta = Path("data/snapshots")
        snapshots = sorted(
            carpeta.glob(f"{self.hypervisor_id}_*.json"),
            key=lambda p: p.stem.removeprefix(f"{self.hypervisor_id}_"),
        )
        sobrantes = len(snapshots) - SNAPSHOT_MAX
        for path in snapshots[:sobrantes]:
            path.unlink(missing_ok=True)
            logger.debug("Snapshot antiguo purgado: %s", path)
