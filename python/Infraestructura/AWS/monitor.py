"""
Monitor de heartbeats por polling (main.py → componentes).

El monitor llama periódicamente a una función ping() por componente.
Si un componente falla N veces seguidas, dispara on_fallo() una única vez.

El diseño con callables (en vez de stubs gRPC directamente) permite:
  - Testear el monitor sin infraestructura real (pasar un ping() que lanza excepción)
  - Cambiar el protocolo de heartbeat sin tocar este módulo
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

logger = logging.getLogger(__name__)


class MonitorComponentes:
    """
    Hace polling concurrente de heartbeat a todos los componentes registrados.
    Si cualquier componente supera el límite de fallos consecutivos, llama
    a on_fallo(componente_id) una sola vez y detiene el monitor.
    """

    def __init__(self, config: dict, on_fallo: Callable[[str], None]):
        self._intervalo: float = config["timeouts"]["heartbeat_intervalo"]
        self._max_perdidos: int = config["timeouts"]["heartbeat_perdidos_max"]
        self._on_fallo = on_fallo

        self._pings: dict[str, Callable[[], None]] = {}
        self._fallos: dict[str, int] = {}
        self._lock = threading.Lock()
        self._activo = False
        self._fallo_disparado = False

    def registrar(self, componente_id: str, ping: Callable[[], None]):
        """
        Registra un componente.

        ping: callable sin argumentos que debe lanzar cualquier excepción si el
              componente no responde. Ejemplo:
                  lambda: stub.Heartbeat(proto.HeartbeatRequest(), timeout=5)
        """
        with self._lock:
            self._pings[componente_id] = ping
            self._fallos[componente_id] = 0

    def iniciar(self):
        self._activo = True
        hilo = threading.Thread(target=self._bucle, daemon=True, name="monitor-heartbeat")
        hilo.start()

    def detener(self):
        """Detiene el monitor limpiamente (no dispara on_fallo)."""
        self._activo = False

    # ------------------------------------------------------------------

    def _poll_uno(self, comp_id: str, ping: Callable[[], None]) -> str | None:
        """
        Llama al ping de un componente.
        Devuelve comp_id si el componente ha fallado demasiadas veces, None si todo bien.
        """
        try:
            ping()
            with self._lock:
                self._fallos[comp_id] = 0
            return None
        except Exception as exc:
            with self._lock:
                self._fallos[comp_id] += 1
                n = self._fallos[comp_id]

            logger.warning(f"[{comp_id}] heartbeat fallido ({n}/{self._max_perdidos}): {exc}")

            if n >= self._max_perdidos:
                return comp_id
            return None

    def _bucle(self):
        while self._activo:
            time.sleep(self._intervalo)

            with self._lock:
                if self._fallo_disparado:
                    return
                pings = dict(self._pings)

            # Polling concurrente: todos los componentes en paralelo
            with ThreadPoolExecutor(max_workers=len(pings)) as executor:
                futuros = {
                    executor.submit(self._poll_uno, comp_id, ping): comp_id
                    for comp_id, ping in pings.items()
                }
                for futuro in as_completed(futuros):
                    if not self._activo:
                        return
                    comp_fallido = futuro.result()
                    if comp_fallido is not None:
                        with self._lock:
                            if self._fallo_disparado:
                                return
                            self._fallo_disparado = True
                        logger.error(
                            f"[{comp_fallido}] sin respuesta — disparando fail-fast"
                        )
                        self.detener()
                        self._on_fallo(comp_fallido)
                        return
