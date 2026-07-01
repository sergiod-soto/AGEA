"""
gestor_bots_server.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).parents[4]))

from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import gestor_bots_service_pb2_grpc
from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots_servicer import Gestor_Bots_Servicer
from Infraestructura.Gestores.Transporte.remote_log_handler import setup_remote_logging
from Utils.Sistema.sistema import registrar_signals

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gestor_bots_server")


async def serve() -> None:
    host = os.getenv("GESTOR_BOTS_HOST", "[::]")
    port = int(os.getenv("GESTOR_BOTS_PORT", 50051))
    workers = int(os.getenv("GESTOR_BOTS_WORKERS", 10))
    bots_por_hv = int(os.getenv("BOTS_POR_HYPERVISOR", 100))
    log_address = os.getenv("LOG_SERVER_ADDRESS", "")
    mundo_address = os.getenv("GESTOR_MUNDO_ADDRESS", "localhost:50200")

    address = f"{host}:{port}"

    if log_address:
        setup_remote_logging(
            mundo_address=log_address,
            component="gestor_bots",
            local_log_path="Logs/Bots/Gestor/gestor_bots.log",
        )

    logger.info(
        "Configuración — host=%s workers=%d bots_por_hv=%d",
        address,
        workers,
        bots_por_hv,
    )

    try:
        from Infraestructura.Gestores.Transporte.hypervisor_client import HypervisorClient

        def hypervisor_client_factory(addr: str, port: int) -> HypervisorClient:
            return HypervisorClient(addr, port)

    except ImportError:
        logger.warning("HypervisorClient no disponible.")
        hypervisor_client_factory = None

    from Infraestructura.Gestores.Transporte.gestor_mundo_client import GestorMundoClient

    mundo_client = GestorMundoClient(mundo_address)

    gestor = Gestor_Bots(
        mundo_client=mundo_client,
        bots_por_hypervisor=bots_por_hv,
    )
    servicer = Gestor_Bots_Servicer(
        gestor=gestor,
        hypervisor_client_factory=hypervisor_client_factory,
    )

    server = grpc.aio.server(
        options=[
            ("grpc.max_receive_message_length", 256 * 1024 * 1024),
            ("grpc.max_send_message_length", 256 * 1024 * 1024),
            ("grpc.keepalive_time_ms", 20_000),
            ("grpc.keepalive_timeout_ms", 10_000),
            ("grpc.keepalive_permit_without_calls", 1),
        ],
    )
    gestor_bots_service_pb2_grpc.add_GestorBotsServiceServicer_to_server(
        servicer, server
    )
    server.add_insecure_port(address)

    await server.start()
    logger.info("Gestor_Bots escuchando en %s (%d workers)", address, workers)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig):
        logger.info("Señal %s — apagando Gestor_Bots...", sig.name)
        loop.call_soon_threadsafe(stop_event.set)

    registrar_signals(loop, _shutdown)

    await stop_event.wait()
    await mundo_client.close()
    await server.stop(grace=5)
    logger.info("Gestor_Bots apagado.")


def main() -> None:
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
