"""
core/log_server.py — Servidor gRPC del LogService.

El Mundo lo arranca al inicializarse. Escucha en un puerto
dedicado exclusivamente a recibir logs de componentes remotos.

Uso desde el Mundo:
    from core.log_server import LogServer

    log_server = LogServer(host="[::]:50060", log_dir="logs/")
    log_server.start()

    # ... simulación corriendo ...

    log_server.stop()

También configura el logger local del Mundo para que escriba
en logs/mundo.log, consistente con el resto de componentes.
"""

from __future__ import annotations

import logging
import logging.handlers
from concurrent import futures
from pathlib import Path

import grpc

from Gestores.Transporte.Proto_Generated.Otros import log_service_pb2_grpc
from Gestores.Mundo.log_servicer import LogServicer

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[3]))  # N = niveles hasta python/


class LogServer:
    """
    Servidor gRPC del LogService.

    Parámetros
    ----------
    host : str
        "host:puerto" en el que escucha (default "[::]:50060").
    log_dir : str | Path
        Directorio de logs (default "logs/").
    workers : int
        Hilos del ThreadPool (default 4; los logs no son CPU-intensivos).
    max_bytes : int
        Tamaño máximo por fichero antes de rotar (default 10 MB).
    backup_count : int
        Ficheros rotados a conservar (default 5).
    """

    def __init__(
        self,
        host: str = "[::]:50060",
        log_dir: str | Path = "Logs/",
        workers: int = 4,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ):
        self._host = host
        self._log_dir = Path(log_dir)

        self._servicer = LogServicer(
            log_dir=log_dir,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )

        self._server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=workers),
            options=[
                ("grpc.max_receive_message_length", 16 * 1024 * 1024),
            ],
        )
        log_service_pb2_grpc.add_LogServiceServicer_to_server(
            self._servicer, self._server
        )
        self._server.add_insecure_port(host)

    def start(self) -> None:
        """Arranca el servidor y configura el log local del Mundo."""
        self._setup_mundo_log()
        self._server.start()
        logging.getLogger(__name__).info(
            "LogServer escuchando en %s — logs en %s/",
            self._host,
            self._log_dir.resolve(),
        )

    def stop(self, grace: float = 3.0) -> None:
        self._server.stop(grace=grace)

    def _setup_mundo_log(self) -> None:
        """
        Configura el logger raíz del Mundo para escribir en:
          - logs/mundo.log  (fichero con rotación)
          - consola          (stdout)

        Llama a esto antes de cualquier otro logging en el Mundo.
        """
        self._log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self._log_dir / "mundo.log"

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Fichero con rotación
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt)
        file_handler.setLevel(logging.DEBUG)

        # Consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(fmt)
        console_handler.setLevel(logging.INFO)

        # Evitar duplicar handlers si se llama varias veces
        if not root.handlers:
            root.addHandler(file_handler)
            root.addHandler(console_handler)
