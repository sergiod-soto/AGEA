# Infraestructura/Gestores/Log/buffered_log_handler.py
"""
buffered_log_handler.py — Handler de logging que ACUMULA en memoria,
en vez de enviar por red (nombre anterior: remote_log_handler.py).

Con el modelo pull, el componente remoto ya no inicia ninguna conexión
para mandar sus logs: solo los guarda en una lista protegida por lock,
y espera a que LogPullServicer.PullLogs() venga a recogerlos y vaciar
el buffer.

Pérdida asumida: si el proceso muere entre dos pulls, los logs
acumulados y no recogidos se pierden. No hay respaldo a disco local
(se podría añadir más adelante si hiciera falta, pero de momento se
prioriza simplicidad).

Uso (en cada _server.py, solo en modo remoto):
    from Infraestructura.Gestores.Log.buffered_log_handler import setup_buffered_logging

    handler = setup_buffered_logging(component="hv_00")
    # ... arranque normal del componente ...
    # `handler` se pasa también al LogPullServicer para que sepa de
    # dónde extraer los logs acumulados.
"""

from __future__ import annotations

import logging
import threading
import time
import traceback
from typing import Optional

from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import log_service_pb2

# Mapeado logging Python → LogLevel protobuf
_PY_TO_PB: dict[int, int] = {
    logging.DEBUG: log_service_pb2.DEBUG,
    logging.INFO: log_service_pb2.INFO,
    logging.WARNING: log_service_pb2.WARNING,
    logging.ERROR: log_service_pb2.ERROR,
    logging.CRITICAL: log_service_pb2.CRITICAL,
}

# Límite del buffer: si nadie hace pull durante mucho tiempo, no
# queremos crecer sin límite y agotar memoria. Al llegar al límite,
# se descartan los registros más antiguos (mismo criterio de
# priorizar WARNING+ que ya usaba la versión push).
_BUFFER_MAX = 5000


class BufferedLogHandler(logging.Handler):
    """
    Handler de logging que acumula LogRecord en memoria, listos para
    ser recogidos por PullLogs().
    """

    def __init__(self, component: str, buffer_max: int = _BUFFER_MAX):
        super().__init__()
        self._component = component
        self._buffer_max = buffer_max
        self._buffer: list[log_service_pb2.LogRecord] = []
        self._lock = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        """Convierte el LogRecord de Python a protobuf y lo acumula."""
        try:
            exc_info = ""
            if record.exc_info:
                exc_info = "".join(traceback.format_exception(*record.exc_info))

            pb_record = log_service_pb2.LogRecord(
                component=self._component,
                level=_PY_TO_PB.get(record.levelno, log_service_pb2.INFO),
                logger=record.name,
                message=self.format(record),
                timestamp=int(record.created * 1000),
                exc_info=exc_info,
            )

            with self._lock:
                self._buffer.append(pb_record)
                if len(self._buffer) > self._buffer_max:
                    # Buffer lleno y nadie ha hecho pull todavía: descartamos
                    # el más antiguo. Igual que en la versión push, se
                    # prioriza no perder WARNING+ sobre DEBUG/INFO.
                    for i, r in enumerate(self._buffer):
                        if r.level < log_service_pb2.WARNING:
                            self._buffer.pop(i)
                            break
                    else:
                        self._buffer.pop(0)

        except Exception:
            self.handleError(record)

    def drain(self) -> list[log_service_pb2.LogRecord]:
        """
        Devuelve todos los registros acumulados y vacía el buffer.
        Llamado por LogPullServicer al recibir PullLogs().
        """
        with self._lock:
            registros = self._buffer
            self._buffer = []
        return registros


def setup_buffered_logging(
    component: str,
    level: int = logging.DEBUG,
) -> BufferedLogHandler:
    """
    Configura el logger raíz del proceso para acumular en un
    BufferedLogHandler, y lo devuelve para que quien llama pueda
    pasárselo al LogPullServicer.
    """
    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = BufferedLogHandler(component=component)
    handler.setFormatter(fmt)
    handler.setLevel(level)
    root.addHandler(handler)

    # Consola: se mantiene, útil para ver el componente en vivo si se
    # inspecciona la instancia EC2 directamente (SSH).
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    console.setLevel(logging.INFO)
    root.addHandler(console)

    return handler
