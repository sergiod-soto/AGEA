"""
gestor_server.py — Arranque del servidor gRPC del Gestor.

Uso:
    python -m Hypervisores.Gestor.gestor_server

Variables de entorno (todas opcionales, tienen default):
    GESTOR_HOST            dirección en la que escucha    (default: "[::]:50051")
    GESTOR_WORKERS         hilos del ThreadPoolExecutor   (default: 10)
    BOTS_POR_HYPERVISOR    bots máximos por HV            (default: 100)
    LOG_LEVEL              nivel de logging               (default: INFO)
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from concurrent import futures

import grpc

from Hypervisores.Transporte.Proto_Generated import gestor_bots_service_pb2_grpc
from Hypervisores.Gestor_Bots.gestor_bots import Gestor_Bots
from Hypervisores.Gestor_Bots.gestor_bots_servicer import Gestor_Bots_Servicer

from Hypervisores.Transporte.remote_log_handler import setup_remote_logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gestor_server")


# ---------------------------------------------------------------------------
# Construcción del servidor
# ---------------------------------------------------------------------------


def build_server(
    host: str = "[::]:50051",
    workers: int = 10,
    mundo_client=None,
    hypervisor_client_factory=None,
    bots_por_hypervisor: int = 100,
) -> tuple[grpc.Server, Gestor_Bots]:
    """
    Construye y devuelve (servidor_grpc, gestor).

    Separar la construcción del arranque permite reutilizarlo en tests
    de integración sin necesitar un proceso aparte.

    Parámetros
    ----------
    host : str
        "host:puerto" en el que escuchará el servidor.
    workers : int
        Número de hilos del pool del servidor gRPC.
    mundo_client : opcional
        Cliente ya conectado al Mundo. None durante tests o si el Mundo
        todavía no ha arrancado (se puede inyectar después con
        gestor.mundo_client = ...).
    hypervisor_client_factory : callable opcional
        (address: str, port: int) → HypervisorClient.
        Si None, el Gestor no podrá llamar a los Hypervisores de vuelta.
    bots_por_hypervisor : int
        Propagado directamente al constructor de Gestor. Es el único punto
        de control de capacidad: determina cuántos bots puede alojar cada HV.
    """
    # 1. Lógica pura
    gestor = Gestor_Bots(
        mundo_client=mundo_client, bots_por_hypervisor=bots_por_hypervisor
    )

    # 2. Servicer gRPC (traduce protobuf ↔ Gestor)
    servicer = Gestor_Bots_Servicer(
        gestor=gestor,
        hypervisor_client_factory=hypervisor_client_factory,
    )

    # 3. Servidor gRPC
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
        "Servidor Gestor construido — host=%s workers=%d bots_por_hv=%d",
        host,
        workers,
        bots_por_hypervisor,
    )
    return server, gestor


# ---------------------------------------------------------------------------
# Arranque principal
# ---------------------------------------------------------------------------


def serve():

    setup_remote_logging(
        mundo_address="10.0.0.1:50060",
        component="gestor_bots",
        local_log_path="logs/gestor_bots_local.log",
    )

    host = os.environ.get("GESTOR_BOTS_HOST", "[::]:50051")
    workers = int(os.environ.get("GESTOR_BOTS_WORKERS", "10"))
    bots_por_hv = int(os.environ.get("BOTS_POR_HYPERVISOR", "100"))

    logger.info(
        "Configuración — host=%s workers=%d bots_por_hypervisor=%d",
        host,
        workers,
        bots_por_hv,
    )

    mundo_client = None

    try:
        from Hypervisores.Transporte.hypervisor_client import HypervisorClient

        def hypervisor_client_factory(address: str, port: int) -> HypervisorClient:
            return HypervisorClient(address, port)

    except ImportError:
        logger.warning(
            "HypervisorClient no disponible todavía; "
            "el Gestor no podrá llamar a los HVs hasta que se implemente."
        )
        hypervisor_client_factory = None

    server, gestor = build_server(
        host=host,
        workers=workers,
        mundo_client=mundo_client,
        hypervisor_client_factory=hypervisor_client_factory,
        bots_por_hypervisor=bots_por_hv,
    )

    server.start()
    logger.info("Gestor_Bots escuchando en %s  (%d workers)", host, workers)

    stop_event = {"fired": False}

    def _shutdown(signum, frame):
        if stop_event["fired"]:
            return
        stop_event["fired"] = True
        logger.info("Señal %d recibida — apagando Gestor_Bots...", signum)
        server.stop(grace=5)
        logger.info("Gestor_Bots apagado.")
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
