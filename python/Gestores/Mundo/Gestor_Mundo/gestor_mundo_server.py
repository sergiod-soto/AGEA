"""
gestor_mundo_server.py
----------------------
Arranca el servidor gRPC del GestorMundo y el bucle de ticks.

Carpeta: Gestores/Mundo/Gestor_Mundo/

Uso:
    python -m Gestores.Mundo.Gestor_Mundo.gestor_mundo_server [--fresh]

    --fresh    Partida nueva. Sin este flag intenta restaurar desde snapshot.
"""

import argparse
import asyncio
import logging
import os
import signal
import sys

import grpc

from Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2_grpc as pb_grpc,
)
from Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
from Gestores.Mundo.Gestor_Mundo.gestor_mundo_servicer import GestorMundoServicer

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[4]))  # N = niveles hasta python/

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  Configuración
# ─────────────────────────────────────────────

GESTOR_MUNDO_HOST = os.getenv("GESTOR_MUNDO_HOST", "[::]:50060")
GESTOR_MUNDO_WORKERS = int(os.getenv("GESTOR_MUNDO_WORKERS", 10))


# ─────────────────────────────────────────────
#  Servidor
# ─────────────────────────────────────────────


async def serve(fresh: bool) -> None:
    gestor = GestorMundo()
    servicer = GestorMundoServicer(gestor)

    server = grpc.aio.server(
        options=[
            # Sin límite de mensaje para el streaming de GetWorldMap
            ("grpc.max_send_message_length", -1),
            ("grpc.max_receive_message_length", -1),
        ]
    )
    pb_grpc.add_GestorMundoServiceServicer_to_server(servicer, server)
    server.add_insecure_port(GESTOR_MUNDO_HOST)

    await server.start()
    logger.info("GestorMundo gRPC escuchando en %s", GESTOR_MUNDO_HOST)

    # Arrancar el gestor (carga estado o inicia limpio)
    await gestor.start(fresh=fresh)

    # Manejar señales de apagado limpio
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig):
        logger.info("Señal %s recibida — apagando...", sig.name)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown, sig)

    # Lanzar el bucle de ticks como tarea paralela
    tick_task = asyncio.create_task(
        _run_tick_loop(gestor),
        name="tick_loop",
    )

    # Esperar señal de apagado
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
    """
    Envuelve gestor.run_loop() para capturar excepciones inesperadas
    y reintentar en lugar de silenciar el fallo.
    """
    while True:
        try:
            await gestor.run_loop()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Error inesperado en el bucle de ticks — reintentando en 1s"
            )
            await asyncio.sleep(1)


# ─────────────────────────────────────────────
#  Entrada
# ─────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="GestorMundo gRPC server")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Iniciar partida nueva (ignora snapshots existentes)",
    )
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
        asyncio.run(serve(fresh=args.fresh))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
