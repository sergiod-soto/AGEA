# Infraestructura/Gestores/Bots/Hypervisor/hypervisor.py
"""
hypervisor.py — Lógica pura del Hypervisor.

CAMBIO: se retira gestor_mundo_client / forward_to_mundo(). Nada los
usaba — world_proxy_servicer._spend_and_forward() solo llama a
forward_to_gestor() en la rama no-delegada; forward_to_mundo() (y su
cliente síncrono, gestor_mundo_client_sync.py) quedaban muertos desde
que se retiró ForwardActionGestorMundo del proto de GestorMundoService.

Vigilancia de procesos (Flujo B de muerte de bots):
  Cada bot corre como un subprocess.Popen independiente. Al lanzarlo,
  se arranca un hilo daemon dedicado (_watch_bot_process) bloqueado en
  proceso.wait() — sin coste de CPU, solo espera de sistema operativo.
  Cuando el proceso termina, el hilo distingue:
    - Terminación deliberada (kill_bot ya quitó el bot de self._bots
      antes de que el proceso muriera) → no hace nada, ya se resolvió.
    - Crash real (el bot seguía registrado) → notifica al Gestor vía
      gestor_client.notificar_avatar_sin_piloto(bot_id), que a su vez
      pide a Logica_Mundo eliminar el avatar del bot en el gold.
  Se eligió un hilo por bot (en vez de un único hilo con sondeo
  periódico) para detección inmediata sin latencia de intervalo, y
  porque el modelo ya es "un proceso por bot" — un hilo más por bot es
  simétrico con eso, no una complejidad añadida distinta.
"""

from __future__ import annotations

import datetime
import gzip
import logging
import os
import sys
import subprocess
import threading
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


@dataclass
class LanzadorProcesosBot:
    """
    Encapsula el despliegue real de un bot: descomprimir su código,
    escribirlo a disco y lanzar el proceso del sistema operativo.

    Se inyecta en Hypervisor en vez de vivir hardcodeado dentro de
    spawn_bot/kill_bot.
    """

    def __init__(self, codigo_dir: Path = Path("bots_codigo")):
        self._codigo_dir = codigo_dir

    def codigo_path(self, hypervisor_id: str, bot_id: str) -> Path:
        return self._codigo_dir / hypervisor_id / f"{bot_id}.py"

    def lanzar(
        self,
        hypervisor_id: str,
        bot_id: str,
        codigo_gz: bytes,
        env_extra: dict,
    ) -> subprocess.Popen:
        """
        Descomprime codigo_gz, lo escribe a disco y lanza el proceso.
        Deja que cualquier excepción se propague tal cual — spawn_bot
        decide qué hacer si falla (deshacer el registro del bot, etc.).
        """
        codigo_path = self.codigo_path(hypervisor_id, bot_id)
        codigo_path.parent.mkdir(parents=True, exist_ok=True)
        codigo_path.write_bytes(gzip.decompress(codigo_gz))

        return subprocess.Popen(
            [sys.executable, str(codigo_path)],
            env={**os.environ, **env_extra},
        )

    def limpiar(self, hypervisor_id: str, bot_id: str) -> None:
        """Elimina el fichero de código del bot, si existe. Idempotente."""
        self.codigo_path(hypervisor_id, bot_id).unlink(missing_ok=True)


class Hypervisor:
    """
    Proxy transparente entre los Bots y el Mundo.

    Parámetros
    ----------
    hypervisor_id      : str
    gestor_client      : GestorBotsClient (síncrono — ver comentario en
                         gestor_bots_client.py sobre por qué el HV usa
                         la versión síncrona, no la async)
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

        self._lock = threading.Lock()
        self._bots: dict[str, BotRecord] = {}
        self._procesos: dict[str, subprocess.Popen] = {}

        self._lanzador = lanzador_procesos or LanzadorProcesosBot()

        self._frozen = False

        # nombre → callable. Poblado en set_delegated_actions.
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
        if not action_names:
            logger.info("HV %s: sin acciones delegadas.", self.hypervisor_id)
            self._delegated = {}
            return

        try:
            from Infraestructura.Gestores.Mundo.Logica_Mundo.api_acciones import (
                ACCIONES,
            )
        except ImportError as exc:
            logger.error("No se pudo importar ACCIONES: %s.", exc)
            self._delegated = {}
            return

        delegated = {}
        for name in action_names:
            entrada = ACCIONES.get(name)
            if entrada is None:
                logger.warning(
                    "Acción delegada '%s' no encontrada en ACCIONES; ignorada.", name
                )
                continue
            fn = entrada.get("funcion")
            if fn is None:
                logger.warning("Acción delegada '%s' no tiene funcion; ignorada.", name)
                continue
            delegated[name] = fn

        self._delegated = delegated
        logger.info(
            "HV %s: acciones delegadas → %s", self.hypervisor_id, list(self._delegated)
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
                ok=False,
                payload=b"",
                error=f"Acción '{action_name}' no está delegada en este HV.",
            )

        with self._lock:
            if bot_id not in self._bots:
                return ActionResult(
                    ok=False, payload=b"", error=f"Bot {bot_id!r} no encontrado."
                )

        from Infraestructura.Gestores.Mundo.Logica_Mundo.api_acciones import (
            AccionContext,
        )

        ctx = AccionContext(
            bot_id=bot_id,
            payload=payload,
        )

        try:
            return fn(ctx)
        except Exception as exc:
            logger.error(
                "Error ejecutando acción delegada '%s' para bot %s: %s",
                action_name,
                bot_id,
                exc,
            )
            return ActionResult(ok=False, payload=b"", error=str(exc))

    # ------------------------------------------------------------------
    # Registro en el Gestor
    # ------------------------------------------------------------------

    def register_with_gestor(self) -> bool:
        result = self.gestor_client.register_hypervisor(
            hypervisor_id=self.hypervisor_id,
            address=self._my_address,
            port=self._my_port,
            proxy_port=self._my_proxy_port,
            capacity=self.capacity,
        )
        if result.ok:
            self.set_delegated_actions(result.delegated_actions)
            logger.info("HV %s registrado correctamente.", self.hypervisor_id)
        else:
            logger.error(
                "Gestor rechazó registro de HV %s: %s", self.hypervisor_id, result.error
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

        with self._lock:
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
            proceso = self._lanzador.lanzar(
                hypervisor_id=self.hypervisor_id,
                bot_id=bot_id,
                codigo_gz=codigo_gz,
                env_extra={
                    "BOT_ID": bot_id,
                    "HV_PROXY_ADDRESS": f"{self._my_address}:{self._my_proxy_port}",
                },
            )
        except Exception as exc:
            with self._lock:
                self._bots.pop(bot_id, None)
            self._lanzador.limpiar(self.hypervisor_id, bot_id)
            logger.error("Error desplegando bot %s: %s", bot_id, exc)
            return SpawnResult(ok=False, error=f"Error desplegando bot: {exc}")

        with self._lock:
            self._bots[bot_id].alive = True
            self._procesos[bot_id] = proceso

        threading.Thread(
            target=self._watch_bot_process,
            args=(bot_id, proceso),
            daemon=True,
            name=f"bot-watcher-{bot_id}",
        ).start()

        logger.info("Bot %s spawneado (budget=%d).", bot_id, budget)
        return SpawnResult(ok=True)

    def _watch_bot_process(self, bot_id: str, proceso: subprocess.Popen) -> None:
        proceso.wait()

        with self._lock:
            crash = bot_id in self._bots
            if crash:
                self._bots.pop(bot_id, None)
                self._procesos.pop(bot_id, None)

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
            self.gestor_client.notificar_avatar_sin_piloto(bot_id)
        except Exception as exc:
            logger.error("Error notificando avatar sin piloto para %s: %s", bot_id, exc)

    def get_bot_stats(self, bot_id: str) -> Optional[BotStats]:
        with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                return None
            return BotStats(
                bot_id=rec.bot_id,
                hypervisor_id=self.hypervisor_id,
                points_left=rec.budget,
                alive=rec.alive,
            )

    def get_bot_status(self, bot_id: str) -> Optional[BotStatusHV]:
        with self._lock:
            rec = self._bots.get(bot_id)
            if rec is None:
                return None
            return BotStatusHV(bot_id=rec.bot_id, alive=rec.alive, budget=rec.budget)

    def list_bots(self) -> BotList:
        with self._lock:
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
            self._lanzador.limpiar(self.hypervisor_id, bot_id)
        except Exception as exc:
            logger.warning("No se pudo eliminar código de %s: %s", bot_id, exc)

        logger.info("Bot %s eliminado.", bot_id)

    # ------------------------------------------------------------------
    # Control de presupuesto
    # ------------------------------------------------------------------

    def try_spend_points(self, bot_id: str, cost: int) -> tuple[bool, int]:
        with self._lock:
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
    # Proxy al Gestor
    # ------------------------------------------------------------------

    def forward_to_gestor(
        self, bot_id: str, action_type: str, payload: bytes
    ) -> ActionResult:
        """Redirige una acción al gestor_bots (para acciones que pasan por él)."""
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

    def freeze(self) -> None:
        with self._lock:
            self._frozen = True
        logger.info("Hypervisor %s congelado.", self.hypervisor_id)

    def resume(self) -> None:
        with self._lock:
            self._frozen = False
        logger.info("Hypervisor %s reanudado.", self.hypervisor_id)

    def save_snapshot(self, snapshot_id: str) -> None:
        import json
        from pathlib import Path

        state = {
            "snapshot_id": snapshot_id,
            "hypervisor_id": self.hypervisor_id,
            "fecha": datetime.datetime.now().isoformat(),
            "bots": [
                {
                    "bot_id": rec.bot_id,
                    "budget": rec.budget,
                    "max_budget": rec.max_budget,
                    "alive": rec.alive,
                }
                for rec in self._bots.values()
            ],
        }
        path = Path("data/snapshots") / f"hv_{self.hypervisor_id}_{snapshot_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state))
        logger.info("Hypervisor %s snapshot guardado: %s", self.hypervisor_id, path)
