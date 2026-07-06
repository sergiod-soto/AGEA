# Infraestructura/Gestores/Log/log_servicer.py
"""
log_servicer.py — Escritura a disco de logs recogidos por pull.

Modelo pull, es main.py quien pregunta a cada componente remoto y
recibe los LogRecord de vuelta. Esta clase solo sabe convertir esos
LogRecord en entradas en el fichero .log correspondiente, categorizado
por componente (ver log_categorias.py).

Se instancia una vez en main.py y se invoca su método escribir() por
cada LogRecord recibido en cada ciclo de polling.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import log_service_pb2
from Infraestructura.Gestores.Log.log_categorias import categoria

logger = logging.getLogger(__name__)

# Mapeado LogLevel protobuf → logging Python
_PB_TO_PY: dict[int, int] = {
    log_service_pb2.DEBUG: logging.DEBUG,
    log_service_pb2.INFO: logging.INFO,
    log_service_pb2.WARNING: logging.WARNING,
    log_service_pb2.ERROR: logging.ERROR,
    log_service_pb2.CRITICAL: logging.CRITICAL,
}


class LogServicer:
    """
    Escribe LogRecord en ficheros de log locales, separados por
    componente y organizados según log_categorias.categoria().

    Parámetros
    ----------
    log_dir : str | Path
        Directorio raíz donde se crearán los ficheros .log.
    max_bytes, backup_count : rotación de cada fichero (igual criterio
        que el resto del proyecto: 10 MB / 5 backups por defecto).
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

    def escribir(self, record: log_service_pb2.LogRecord) -> None:
        """Escribe un LogRecord en el fichero del componente correspondiente."""
        logger_componente = self._get_logger(record.component)
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

        logger_componente.handle(py_record)

    def _get_logger(self, component: str) -> logging.Logger:
        """Devuelve (o crea) el logger Python para un componente."""
        if component in self._loggers:
            return self._loggers[component]

        subcarpeta = categoria(component)
        if subcarpeta == Path("."):
            logger.warning(
                "Componente sin categoría de carpeta asignada: %s "
                "(log en la raíz de %s)",
                component,
                self._log_dir,
            )

        log_dir_componente = self._log_dir / subcarpeta
        log_dir_componente.mkdir(parents=True, exist_ok=True)

        logger_name = f"remote.{component}"
        logger_componente = logging.getLogger(logger_name)
        logger_componente.setLevel(logging.DEBUG)
        logger_componente.propagate = False  # no sube al logger raíz

        log_path = log_dir_componente / f"{component}.log"
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
        logger_componente.addHandler(handler)

        self._loggers[component] = logger_componente
        return logger_componente
