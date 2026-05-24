"""
gestor_server.py — Arranque del servidor gRPC del Gestor.

Uso:
    python -m Hypervisores.Gestor.gestor_server

Variables de entorno (todas opcionales, tienen default):
    GESTOR_HOST      dirección en la que escucha    (default: "[::]:50051")
    GESTOR_WORKERS   hilos del ThreadPoolExecutor   (default: 10)
    LOG_LEVEL        nivel de logging               (default: INFO)
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from concurrent import futures

import grpc

from Hypervisores.Transporte.Proto_Generated import gestor_service_pb2_grpc
from Hypervisores.Gestor.gestor import Gestor
from Hypervisores.Gestor.gestor_servicer import GestorServicer

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
) -> tuple[grpc.Server, Gestor]:
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
    """
    # 1. Lógica pura
    gestor = Gestor(mundo_client=mundo_client)

    # 2. Servicer gRPC (traduce protobuf ↔ Gestor)
    servicer = GestorServicer(
        gestor=gestor,
        hypervisor_client_factory=hypervisor_client_factory,
    )

    # 3. Servidor gRPC
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=workers),
        options=[
            # Máximo 256 MB por mensaje (útil si el genoma es grande)
            ("grpc.max_receive_message_length", 256 * 1024 * 1024),
            ("grpc.max_send_message_length",    256 * 1024 * 1024),
            # Keepalive: detecta hypervisores caídos
            ("grpc.keepalive_time_ms",              20_000),
            ("grpc.keepalive_timeout_ms",           10_000),
            ("grpc.keepalive_permit_without_calls",       1),
        ],
    )

    gestor_service_pb2_grpc.add_GestorServiceServicer_to_server(servicer, server)
    server.add_insecure_port(host)

    return server, gestor


# ---------------------------------------------------------------------------
# Arranque principal
# ---------------------------------------------------------------------------

def serve():
    host    = os.environ.get("GESTOR_HOST", "[::]:50051")
    workers = int(os.environ.get("GESTOR_WORKERS", "10"))

    # En producción, aquí se importa y construye el MundoClient real.
    # Por ahora lo dejamos None; el Gestor funciona sin él
    # (forward_action devuelve un stub vacío).
    mundo_client = None

    # Factory para crear clientes hacia los Hypervisores.
    # Se importa aquí (no en el módulo) para evitar imports circulares.
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
    )

    server.start()
    logger.info("Gestor escuchando en %s  (%d workers)", host, workers)

    # Apagado limpio con Ctrl+C o SIGTERM
    stop_event = {"fired": False}

    def _shutdown(signum, frame):
        if stop_event["fired"]:
            return
        stop_event["fired"] = True
        logger.info("Señal %d recibida — apagando Gestor...", signum)
        server.stop(grace=5)          # 5 s de gracia para RPCs en vuelo
        logger.info("Gestor apagado.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Bucle de espera
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        _shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    serve()
