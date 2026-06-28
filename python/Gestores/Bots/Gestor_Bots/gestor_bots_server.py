"""
gestor_bots_server.py
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from concurrent import futures
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).parents[4]))

from Gestores.Transporte.Proto_Generated.Bots import gestor_bots_service_pb2_grpc
from Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
from Gestores.Bots.Gestor_Bots.gestor_bots_servicer import Gestor_Bots_Servicer
from Gestores.Transporte.remote_log_handler import setup_remote_logging

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gestor_bots_server")


def build_server(
    host: str,
    workers: int,
    mundo_client=None,
    hypervisor_client_factory=None,
    bots_por_hypervisor: int = 100,
) -> tuple[grpc.Server, Gestor_Bots]:
    gestor = Gestor_Bots(
        mundo_client=mundo_client,
        bots_por_hypervisor=bots_por_hypervisor,
    )
    servicer = Gestor_Bots_Servicer(
        gestor=gestor,
        hypervisor_client_factory=hypervisor_client_factory,
    )
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=workers),
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
    server.add_insecure_port(host)

    logger.info(
        "Servidor Gestor_Bots construido — host=%s workers=%d bots_por_hv=%d",
        host,
        workers,
        bots_por_hypervisor,
    )
    return server, gestor


def serve():
    host = os.getenv("GESTOR_BOTS_HOST", "[::]")
    port = int(os.getenv("GESTOR_BOTS_PORT", 50051))
    workers = int(os.getenv("GESTOR_BOTS_WORKERS", 10))
    bots_por_hv = int(os.getenv("BOTS_POR_HYPERVISOR", 100))
    log_address = os.getenv("LOG_SERVER_ADDRESS", "")  # vacío = sin log remoto

    address = f"{host}:{port}"

    logger.info(
        "Configuración — host=%s workers=%d bots_por_hypervisor=%d",
        address,
        workers,
        bots_por_hv,
    )

    # Log remoto solo si hay dirección configurada
    if log_address:
        setup_remote_logging(
            mundo_address=log_address,
            component="gestor_bots",
            local_log_path="Logs/Bots/Gestor/gestor_bots.log",
        )

    mundo_client = None

    try:
        from Gestores.Transporte.hypervisor_client import HypervisorClient

        def hypervisor_client_factory(address: str, port: int) -> HypervisorClient:
            return HypervisorClient(address, port)

    except ImportError:
        logger.warning("HypervisorClient no disponible.")
        hypervisor_client_factory = None

    server, gestor = build_server(
        host=address,
        workers=workers,
        mundo_client=mundo_client,
        hypervisor_client_factory=hypervisor_client_factory,
        bots_por_hypervisor=bots_por_hv,
    )

    server.start()
    logger.info("Gestor_Bots escuchando en %s (%d workers)", address, workers)

    stop_event = {"fired": False}

    def _shutdown(signum, frame):
        if stop_event["fired"]:
            return
        stop_event["fired"] = True
        logger.info("Señal %d recibida — apagando Gestor_Bots...", signum)
        server.stop(grace=5)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        _shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    serve()
