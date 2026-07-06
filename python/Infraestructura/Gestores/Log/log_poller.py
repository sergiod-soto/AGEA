# Infraestructura/Gestores/Log/log_poller.py
"""
log_poller.py — Hilo de polling que recoge logs de componentes remotos.

Modelo pull: este poller corre en la máquina local (dentro de remote.py)
y pregunta periódicamente a cada componente remoto por sus logs
acumulados (RPC PullLogs), escribiéndolos a disco vía LogServicer.

Deliberadamente separado de MonitorComponentes (monitor.py): ese monitor
es fail-fast (si un componente no responde N veces, dispara apagado de
todo el sistema). Aquí un fallo puntual de PullLogs no debe apagar nada
— solo se loguea como warning y se reintenta en el siguiente ciclo.
"""

import logging
import threading
import time
from typing import Callable

logger = logging.getLogger(__name__)


class LogPoller:
    """
    Polling periódico de PullLogs sobre un conjunto de componentes,
    escribiendo lo recibido vía la función `escribir` inyectada
    (normalmente LogServicer.escribir).

    No es fail-fast: un fallo de un componente en un ciclo no afecta a
    los demás ni detiene el poller — se reintenta en el siguiente ciclo.
    """

    def __init__(self, intervalo_segundos: float, escribir: Callable):
        self._intervalo = intervalo_segundos
        self._escribir = escribir
        self._pulls: dict[str, Callable[[], list]] = {}
        self._lock = threading.Lock()
        self._activo = False

    def registrar(self, componente_id: str, pull: Callable[[], list]) -> None:
        """
        pull: callable sin argumentos que devuelve list[LogRecord]
        (el resultado de stub.PullLogs(...).records), o lanza excepción
        si falla la llamada — el poller la captura y sigue con el resto.
        """
        with self._lock:
            self._pulls[componente_id] = pull

    def iniciar(self) -> None:
        self._activo = True
        hilo = threading.Thread(target=self._bucle, daemon=True, name="log-poller")
        hilo.start()

    def detener(self) -> None:
        """Detiene el poller limpiamente (no intenta un último pull)."""
        self._activo = False

    def _bucle(self) -> None:
        while self._activo:
            time.sleep(self._intervalo)
            with self._lock:
                pulls = dict(self._pulls)
            for comp_id, pull in pulls.items():
                if not self._activo:
                    return
                try:
                    for registro in pull():
                        self._escribir(registro)
                except Exception as exc:
                    # Fallo puntual: se loguea y se sigue con el resto.
                    # A propósito NO es fail-fast (a diferencia de
                    # MonitorComponentes) — perder logs de un ciclo no
                    # justifica apagar el sistema.
                    logger.warning(
                        "[%s] fallo al recoger logs (se reintenta en %ss): %s",
                        comp_id,
                        self._intervalo,
                        exc,
                    )
