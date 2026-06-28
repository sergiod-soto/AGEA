"""
hypervisor_server.py
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
import threading
from concurrent import futures
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).parents[4]))

from Gestores.Transporte.Proto_Generated.Bots import (
    hypervisor_service_pb2_grpc,
    world_proxy_service_pb2_grpc,
)
from Gestores.Transporte.gestor_bots_client import GestorBotsClient
from Gestores.Bots.Hypervisor.hypervisor import Hypervisor
from Gestores.Bots.Hypervisor.hypervisor_servicer import HypervisorServicer
from Gestores.Bots.Hypervisor.world_proxy_servicer import WorldProxyServicer
from Gestores.Transporte.remote_log_handler import setup_remote_logging

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("hypervisor_server")

_GRPC_OPTIONS = [
    ("grpc.max_receive_message_length", 256 * 1024 * 1024),
    ("grpc.max_send_message_length", 256 * 1024 * 1024),
    ("grpc.keepalive_time_ms", 20_000),
    ("grpc.keepalive_timeout_ms", 10_000),
    ("grpc.keepalive_permit_without_calls", 1),
]


def build_servers(
    hv_id: str,
    my_address: str,
    my_port: int,
    my_proxy_port: int,
    capacity: int,
    workers: int,
    gestor_address: str,
) -> tuple[grpc.Server, grpc.Server, Hypervisor, GestorBotsClient]:
    gestor_client = GestorBotsClient(gestor_address)
    hv = Hypervisor(
        hypervisor_id=hv_id,
        gestor_client=gestor_client,
        capacity=capacity,
        my_address=my_address,
        my_port=my_port,
        my_proxy_port=my_proxy_port,
    )

    management_server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=workers), options=_GRPC_OPTIONS
    )
    hypervisor_service_pb2_grpc.add_HypervisorServiceServicer_to_server(
        HypervisorServicer(hv), management_server
    )
    management_server.add_insecure_port(f"[::]:{my_port}")

    proxy_server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=workers), options=_GRPC_OPTIONS
    )
    world_proxy_service_pb2_grpc.add_WorldProxyServiceServicer_to_server(
        WorldProxyServicer(hv), proxy_server
    )
    proxy_server.add_insecure_port(f"[::]:{my_proxy_port}")

    return management_server, proxy_server, hv, gestor_client


def serve():
    # Variables alineadas con lo que inyecta main.py
    hv_id = os.getenv("HYPERVISOR_ID", "hv_00")
    my_address = os.getenv("HYPERVISOR_HOST", "localhost")
    my_port = int(os.getenv("HYPERVISOR_PORT", 50300))
    my_proxy_port = int(os.getenv("HYPERVISOR_PROXY_PORT", 50400))
    capacity = int(os.getenv("HYPERVISOR_CAPACITY", 32))
    workers = int(os.getenv("HYPERVISOR_WORKERS", 10))
    gestor_address = os.getenv("GESTOR_BOTS_ADDRESS", "localhost:50051")
    log_address = os.getenv("LOG_SERVER_ADDRESS", "")

    # Log remoto solo si hay dirección configurada
    if log_address:
        setup_remote_logging(
            mundo_address=log_address,
            component=hv_id,
            local_log_path=f"Logs/Bots/Hypervisor/{hv_id}.log",
        )

    management_server, proxy_server, hv, gestor_client = build_servers(
        hv_id=hv_id,
        my_address=my_address,
        my_port=my_port,
        my_proxy_port=my_proxy_port,
        capacity=capacity,
        workers=workers,
        gestor_address=gestor_address,
    )

    management_server.start()
    logger.info("HypervisorService arrancado en [::]:%d", my_port)

    proxy_server.start()
    logger.info("WorldProxyService arrancado en [::]:%d", my_proxy_port)

    _register_with_retries(hv)

    def _heartbeat():
        while True:
            time.sleep(30)
            try:
                hv.report_load()
            except Exception as exc:
                logger.warning("Heartbeat fallido: %s", exc)

    threading.Thread(target=_heartbeat, daemon=True, name="hv-heartbeat").start()

    stop_event = {"fired": False}

    def _shutdown(signum, frame):
        if stop_event["fired"]:
            return
        stop_event["fired"] = True
        logger.info("Señal %d — apagando Hypervisor %s...", signum, hv_id)
        management_server.stop(grace=5)
        proxy_server.stop(grace=5)
        gestor_client.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        _shutdown(signal.SIGINT, None)


def _register_with_retries(hv: Hypervisor, retries: int = 10, delay: float = 2.0):
    for attempt in range(1, retries + 1):
        try:
            if hv.register_with_gestor():
                return
            logger.warning("Registro rechazado (intento %d/%d).", attempt, retries)
        except Exception as exc:
            logger.warning(
                "No se pudo contactar con Gestor (intento %d/%d): %s",
                attempt,
                retries,
                exc,
            )
        time.sleep(delay)
    logger.error("No se pudo registrar tras %d intentos.", retries)


if __name__ == "__main__":
    serve()
