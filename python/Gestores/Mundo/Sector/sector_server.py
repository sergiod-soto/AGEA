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
"""

import asyncio
import logging
import os
import signal

import grpc

from Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2_grpc as pb_grpc,
)
from Gestores.Mundo.Sector.sector import Sector
from Gestores.Mundo.Sector.sector_servicer import SectorServicer

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[4]))  # N = niveles hasta python/

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  Configuración
# ─────────────────────────────────────────────

SECTOR_COL = int(os.getenv("SECTOR_COL", 0))
SECTOR_ROW = int(os.getenv("SECTOR_ROW", 0))
SECTOR_HOST = os.getenv("SECTOR_HOST", "[::]")
SECTOR_BASE_PORT = int(os.getenv("SECTOR_BASE_PORT", 50100))
SECTOR_WORKERS = int(os.getenv("SECTOR_WORKERS", 4))

# Número de filas de sectores — necesario para calcular el puerto
ROWS = int(os.getenv("ROWS", 10))  # ceil(GRID_HEIGHT / SECTOR_SIZE)


def _sector_port() -> int:
    return SECTOR_BASE_PORT + SECTOR_COL * ROWS + SECTOR_ROW


# ─────────────────────────────────────────────
#  Servidor
# ─────────────────────────────────────────────


async def serve() -> None:
    sector = Sector()
    servicer = SectorServicer(sector)

    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", -1),
            ("grpc.max_receive_message_length", -1),
        ]
    )
    pb_grpc.add_SectorServiceServicer_to_server(servicer, server)

    address = f"{SECTOR_HOST}:{_sector_port()}"
    server.add_insecure_port(address)

    await server.start()
    logger.info(
        "Sector (%d,%d) gRPC escuchando en %s",
        SECTOR_COL,
        SECTOR_ROW,
        address,
    )

    # Apagado limpio
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig):
        logger.info(
            "Señal %s recibida — apagando sector (%d,%d)...",
            sig.name,
            SECTOR_COL,
            SECTOR_ROW,
        )
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown, sig)

    await stop_event.wait()

    logger.info("Apagando servidor gRPC del sector (%d,%d)...", SECTOR_COL, SECTOR_ROW)
    await server.stop(grace=5)
    logger.info("Sector (%d,%d) detenido.", SECTOR_COL, SECTOR_ROW)


# ─────────────────────────────────────────────
#  Entrada
# ─────────────────────────────────────────────


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
