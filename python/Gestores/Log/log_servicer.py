"""
Gestores/Log/log_servicer.py — Implementación gRPC del LogService.

Vive en el Mundo (local). Recibe logs del Gestor y los Hypervisores
(ambos en AWS) y los escribe en disco organizados por componente.

Estructura de ficheros generada en logs/:
    logs/
    ├── gestor.log
    ├── hv_01.log
    ├── hv_02.log
    └── mundo.log      ← el Mundo escribe el suyo directamente (no via gRPC)
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from Gestores.Transporte.Proto_Generated.Otros import (
    log_service_pb2,
    log_service_pb2_grpc,
)

# ---------------------------------------------------------------------------
# Mapeado LogLevel protobuf → logging Python
# ---------------------------------------------------------------------------
_PB_TO_PY: dict[int, int] = {
    log_service_pb2.DEBUG: logging.DEBUG,
    log_service_pb2.INFO: logging.INFO,
    log_service_pb2.WARNING: logging.WARNING,
    log_service_pb2.ERROR: logging.ERROR,
    log_service_pb2.CRITICAL: logging.CRITICAL,
}


class LogServicer(log_service_pb2_grpc.LogServiceServicer):
    """
    Recibe LogRecord / LogBatch de componentes remotos y los
    escribe en ficheros de log locales separados por componente.

    Parámetros
    ----------
    log_dir : str | Path
        Directorio donde se crearán los ficheros .log.
        Se crea si no existe.
    max_bytes : int
        Tamaño máximo de cada fichero antes de rotar (default 10 MB).
    backup_count : int
        Número de ficheros rotados a conservar (default 5).
    """

    def __init__(
        self,
        log_dir: str | Path = "Logs/",
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ):
        self._log_dir = Path(log_dir)
        self._max_bytes = max_bytes
        self._backup_count = backup_count
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # Caché de loggers Python por componente para no recrearlos
        self._loggers: dict[str, logging.Logger] = {}

        logging.getLogger(__name__).info(
            "LogServicer iniciado. Logs en: %s", self._log_dir.resolve()
        )

    # ------------------------------------------------------------------
    # RPCs
    # ------------------------------------------------------------------

    def SendLog(self, request, context):
        self._write(request)
        return log_service_pb2.LogAck(ok=True)

    def SendBatch(self, request, context):
        for record in request.records:
            self._write(record)
        return log_service_pb2.LogAck(ok=True)

    # ------------------------------------------------------------------
    # Escritura en disco
    # ------------------------------------------------------------------

    def _write(self, record: log_service_pb2.LogRecord) -> None:
        """Escribe un LogRecord en el fichero del componente correspondiente."""
        logger = self._get_logger(record.component)
        level = _PB_TO_PY.get(record.level, logging.INFO)

        # Reconstruimos un LogRecord Python para que el formatter lo procese
        py_record = logging.LogRecord(
            name=record.logger or record.component,
            level=level,
            pathname="",
            lineno=0,
            msg=record.message,
            args=(),
            exc_info=None,
        )
        # Sustituimos el tiempo por el timestamp original del componente remoto
        py_record.created = record.timestamp / 1000.0
        py_record.msecs = record.timestamp % 1000
        py_record.exc_text = record.exc_info or None

        logger.handle(py_record)

    def _get_logger(self, component: str) -> logging.Logger:
        """
        Devuelve (o crea) el logger Python para un componente.
        Cada componente escribe en su propio fichero con rotación.
        """
        if component in self._loggers:
            return self._loggers[component]

        # Nombre único para evitar colisiones con el logger raíz
        logger_name = f"remote.{component}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # no sube al logger raíz

        # Fichero con rotación por tamaño
        log_path = self._log_dir / f"{component}.log"
        handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=self._max_bytes,
            backupCount=self._backup_count,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

        self._loggers[component] = logger
        logging.getLogger(__name__).info(
            "Nuevo componente registrado para logs: %s → %s",
            component,
            log_path,
        )
        return logger
