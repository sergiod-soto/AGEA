"""
gestor_mundo_server.py
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).parents[4]))

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2_grpc as pb_grpc,
)
from Config.settings import FRESH
from Utils.Sistema.sistema import registrar_signals
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo_servicer import (
    GestorMundoServicer,
)

logger = logging.getLogger(__name__)

GESTOR_MUNDO_HOST = os.getenv("GESTOR_MUNDO_HOST", "[::]")
GESTOR_MUNDO_PORT = int(os.getenv("GESTOR_MUNDO_PORT", 50200))
GESTOR_MUNDO_WORKERS = int(os.getenv("GESTOR_MUNDO_WORKERS", 10))
LOG_SERVER_ADDRESS = os.getenv("LOG_SERVER_ADDRESS", "")  # vacío = sin log remoto


async def serve(fresh: bool) -> None:
    gestor = GestorMundo()
    servicer = GestorMundoServicer(gestor)

    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", -1),
            ("grpc.max_receive_message_length", -1),
        ]
    )
    pb_grpc.add_GestorMundoServiceServicer_to_server(servicer, server)

    address = f"{GESTOR_MUNDO_HOST}:{GESTOR_MUNDO_PORT}"
    server.add_insecure_port(address)
    await server.start()
    logger.info("GestorMundo gRPC escuchando en %s", address)

    await gestor.start(fresh=fresh)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig):
        logger.info("Señal %s recibida — apagando...", sig.name)
        loop.call_soon_threadsafe(stop_event.set)

    registrar_signals(loop, _shutdown)

    tick_task = asyncio.create_task(_run_tick_loop(gestor), name="tick_loop")

    await stop_event.wait()

    logger.info("Deteniendo bucle de ticks...")
    tick_task.cancel()
    try:
        await tick_task
    except asyncio.CancelledError:
        pass

    logger.info("Apagando servidor gRPC...")
    await server.stop(grace=5)
    logger.info("GestorMundo detenido.")


async def _run_tick_loop(gestor: GestorMundo) -> None:
    while True:
        try:
            await gestor.run_loop()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error en bucle de ticks — reintentando en 1s")
            await asyncio.sleep(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        asyncio.run(serve(fresh=FRESH))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
