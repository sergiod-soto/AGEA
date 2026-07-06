# Infraestructura/Gestores/Mundo/Sector/sector_server.py
"""
sector_server.py
----------------
Arranca el servidor gRPC del Sector.
Carpeta: Gestores/Mundo/Sector/
Uso:
    python -m Gestores.Mundo.Sector.sector_server
Variables de entorno relevantes:
    SECTOR_COL, SECTOR_ROW
    SECTOR_HOST, SECTOR_BASE_PORT   (puerto = BASE_PORT + col * ROWS + row)
    SECTOR_WORKERS
    LOG_LEVEL
    MODO ("local" o "remoto"/"produccion" — decide logging directo a
          fichero vs. buffer + PullLogs; ver Config/settings.py)
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).parents[4]))

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import (
    log_pull_service_pb2_grpc,
)
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
from Infraestructura.Gestores.Mundo.Sector.sector_servicer import SectorServicer
from Infraestructura.Gestores.Log.local_logging import setup_local_logging
from Infraestructura.Gestores.Log.buffered_log_handler import setup_buffered_logging
from Infraestructura.Gestores.Log.log_pull_servicer import LogPullServicerAsync
from Utils.Sistema.sistema import registrar_signals
from Config.settings import MODO, LOG_DIR

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  Configuración
# ─────────────────────────────────────────────

SECTOR_COL = int(os.getenv("SECTOR_COL", 0))
SECTOR_ROW = int(os.getenv("SECTOR_ROW", 0))
SECTOR_HOST = os.getenv("SECTOR_HOST", "[::]")
SECTOR_BASE_PORT = int(os.getenv("SECTOR_BASE_PORT", 50100))
SECTOR_WORKERS = int(os.getenv("SECTOR_WORKERS", 4))
ROWS = int(os.getenv("ROWS", 10))


def _sector_port() -> int:
    return SECTOR_BASE_PORT + SECTOR_COL * ROWS + SECTOR_ROW


def _component_id() -> str:
    # Coincide con el prefijo "sector_" registrado en log_categorias.py
    return f"sector_{SECTOR_COL}_{SECTOR_ROW}"


# ─────────────────────────────────────────────
#  Servidor
# ─────────────────────────────────────────────


async def serve(log_level: int) -> None:
    # Logging: única fuente de verdad para configurar el logger raíz.
    # En local escribe directo a fichero; en remoto acumula en memoria y
    # expone PullLogs para que remote.py (en el ordenador local) lo recoja.
    if MODO == "local":
        setup_local_logging(component=_component_id(), log_dir=LOG_DIR, level=log_level)
    else:
        log_handler = setup_buffered_logging(component=_component_id(), level=log_level)

    sector = Sector()
    servicer = SectorServicer(sector)

    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", -1),
            ("grpc.max_receive_message_length", -1),
        ]
    )
    pb_grpc.add_SectorServiceServicer_to_server(servicer, server)

    if MODO != "local":
        # Se registra en el MISMO servidor y puerto — no se abre uno nuevo.
        log_pull_service_pb2_grpc.add_LogPullServiceServicer_to_server(
            LogPullServicerAsync(log_handler), server
        )

    address = f"{SECTOR_HOST}:{_sector_port()}"
    server.add_insecure_port(address)
    await server.start()

    logger.info("Sector (%d,%d) gRPC escuchando en %s", SECTOR_COL, SECTOR_ROW, address)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig):
        logger.info(
            "Señal %s recibida — apagando sector (%d,%d)...",
            sig.name,
            SECTOR_COL,
            SECTOR_ROW,
        )
        loop.call_soon_threadsafe(stop_event.set)

    registrar_signals(loop, _shutdown)

    await stop_event.wait()
    logger.info("Apagando servidor gRPC del sector (%d,%d)...", SECTOR_COL, SECTOR_ROW)
    await server.stop(grace=5)
    logger.info("Sector (%d,%d) detenido.", SECTOR_COL, SECTOR_ROW)


# ─────────────────────────────────────────────
#  Entrada
# ─────────────────────────────────────────────


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()
    log_level = getattr(logging, args.log_level)

    # Ya no hay logging.basicConfig() aquí: setup_local_logging /
    # setup_buffered_logging (llamados dentro de serve()) son los únicos
    # que configuran el logger raíz, para evitar que basicConfig() añada
    # un StreamHandler antes de tiempo y bloquee silenciosamente el guard
    # "if not root.handlers" de esas funciones.
    try:
        asyncio.run(serve(log_level=log_level))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
