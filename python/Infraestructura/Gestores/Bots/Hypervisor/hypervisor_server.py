# Infraestructura/Gestores/Bots/Hypervisor/hypervisor_server.py
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

from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    hypervisor_service_pb2_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import (
    log_pull_service_pb2_grpc,
)
from Infraestructura.Gestores.Transporte.gestor_mundo_client_sync import (
    GestorMundoClientSync,
)

sys.path.insert(0, str(Path(__file__).parents[4]))

from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    world_proxy_service_pb2_grpc,
)
from Infraestructura.Gestores.Transporte.gestor_bots_client import GestorBotsClient
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor_servicer import (
    HypervisorServicer,
)
from Infraestructura.Gestores.Bots.Hypervisor.world_proxy_servicer import (
    WorldProxyServicer,
)
from Infraestructura.Gestores.Log.local_logging import setup_local_logging
from Infraestructura.Gestores.Log.buffered_log_handler import setup_buffered_logging
from Infraestructura.Gestores.Log.log_pull_servicer import LogPullServicer
from Config.settings import MODO, LOG_DIR

logger = logging.getLogger("hypervisor_server")

_GRPC_OPTIONS = [
    ("grpc.max_receive_message_length", 256 * 1024 * 1024),
    ("grpc.max_send_message_length", 256 * 1024 * 1024),
    ("grpc.keepalive_time_ms", 20_000),
    ("grpc.keepalive_timeout_ms", 10_000),
]


def build_servers(
    hv_id: str,
    my_address: str,
    my_port: int,
    my_proxy_port: int,
    capacity: int,
    workers: int,
    gestor_address: str,
    gestor_mundo_address: str,
) -> tuple[grpc.Server, grpc.Server, Hypervisor, GestorBotsClient]:
    gestor_client = GestorBotsClient(gestor_address)
    # Cliente síncrono hacia el Mundo (ver gestor_mundo_client_sync.py
    # para el porqué: el Hypervisor no corre ningún event loop asyncio).
    gestor_mundo_client = GestorMundoClientSync(gestor_mundo_address)
    hv = Hypervisor(
        hypervisor_id=hv_id,
        gestor_client=gestor_client,
        gestor_mundo_client=gestor_mundo_client,
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
    gestor_mundo_address = os.getenv("GESTOR_MUNDO_ADDRESS", "localhost:50200")
    hv_id = os.getenv("HYPERVISOR_ID", "hv_00")
    my_address = os.getenv("HYPERVISOR_HOST", "localhost")
    my_port = int(os.getenv("HYPERVISOR_PORT", 50300))
    my_proxy_port = int(os.getenv("HYPERVISOR_PROXY_PORT", 50400))
    capacity = int(os.getenv("HYPERVISOR_CAPACITY", 32))
    workers = int(os.getenv("HYPERVISOR_WORKERS", 10))
    gestor_address = os.getenv("GESTOR_BOTS_ADDRESS", "localhost:50051")
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())

    # Logging: única fuente de verdad (sin logging.basicConfig() en
    # paralelo — decisión ya tomada para los otros _server.py, mismo
    # motivo aquí). En local escribe directo a fichero; en remoto acumula
    # en memoria y expone PullLogs sobre el MISMO servidor y puerto que
    # HypervisorService (management_server) — no se abre un puerto nuevo.
    if MODO == "local":
        setup_local_logging(component=hv_id, log_dir=LOG_DIR, level=log_level)
    else:
        log_handler = setup_buffered_logging(component=hv_id, level=log_level)

    management_server, proxy_server, hv, gestor_client = build_servers(
        hv_id=hv_id,
        my_address=my_address,
        my_port=my_port,
        my_proxy_port=my_proxy_port,
        capacity=capacity,
        workers=workers,
        gestor_address=gestor_address,
        gestor_mundo_address=gestor_mundo_address,
    )

    if MODO != "local":
        log_pull_service_pb2_grpc.add_LogPullServiceServicer_to_server(
            LogPullServicer(log_handler), management_server
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
        # Antes no se cerraba explícitamente: se añade aquí por
        # consistencia (mismo criterio que gestor_client.close()).
        hv.gestor_mundo_client.close()
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
