# Infraestructura/Gestores/Log/local_logging.py
"""
local_logging.py — Configura logging directo a fichero cuando el
componente corre en modo local (misma máquina que main.py).

No hay red de por medio: se escribe directamente en Logs/<categoria>/
usando el mismo criterio de carpetas que el modo remoto (log_categorias),
para que la estructura de Logs/ sea idéntica en ambos modos.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from Infraestructura.Gestores.Log.log_categorias import categoria

logger = logging.getLogger(__name__)


def setup_local_logging(
    component: str,
    log_dir: str | Path = "Logs/",
    level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """Configura el logger raíz del proceso para escribir directo a fichero."""
    log_dir = Path(log_dir)
    subcarpeta = categoria(component)
    if subcarpeta == Path("."):
        logger.warning(
            "Componente sin categoría de carpeta asignada: %s "
            "(log en la raíz de %s)",
            component,
            log_dir,
        )

    log_dir_componente = log_dir / subcarpeta
    log_dir_componente.mkdir(parents=True, exist_ok=True)
    log_path = log_dir_componente / f"{component}.log"

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.INFO)

    if not root.handlers:
        root.addHandler(file_handler)
        root.addHandler(console_handler)
