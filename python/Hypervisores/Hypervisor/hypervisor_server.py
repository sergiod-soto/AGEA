"""
hypervisor_server.py — Arranque del Hypervisor.

Levanta dos servidores gRPC en el mismo proceso:
  - HypervisorService  (puerto HV_PORT)       ← escucha al Gestor
  - WorldProxyService  (puerto HV_PROXY_PORT) ← escucha a los Bots

Tras arrancar ambos servidores se registra en el Gestor automáticamente.

Uso:
    python -m Hypervisores.Hypervisor.hypervisor_server

Variables de entorno (todas opcionales):
    HV_ID           identificador único de este HV       (default: "hv_01")
    HV_ADDRESS      IP/hostname accesible desde fuera    (default: "localhost")
    HV_PORT         puerto del HypervisorService         (default: 50052)
    HV_PROXY_PORT   puerto del WorldProxyService         (default: 50053)
    HV_CAPACITY     slots de bots simultáneos            (default: 32)
    HV_WORKERS      hilos por servidor gRPC              (default: 10)
    GESTOR_ADDRESS  host:puerto del Gestor               (default: "localhost:50051")
    LOG_LEVEL       nivel de logging                     (default: INFO)
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from concurrent import futures

import grpc

from Hypervisores.Transporte.Proto_Generated import (
    hypervisor_service_pb2_grpc,
    world_proxy_service_pb2_grpc,
)
from Hypervisores.Transporte.gestor_client import GestorClient
from Hypervisores.Hypervisor.hypervisor import Hypervisor
from Hypervisores.Hypervisor.hypervisor_servicer import HypervisorServicer
from Hypervisores.Hypervisor.world_proxy_servicer import WorldProxyServicer

from Hypervisores.Transporte.remote_log_handler import setup_remote_logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("hypervisor_server")

# ---------------------------------------------------------------------------
# Opciones gRPC comunes
# ---------------------------------------------------------------------------
_GRPC_OPTIONS = [
    ("grpc.max_receive_message_length", 256 * 1024 * 1024),
    ("grpc.max_send_message_length", 256 * 1024 * 1024),
    ("grpc.keepalive_time_ms", 20_000),
    ("grpc.keepalive_timeout_ms", 10_000),
    ("grpc.keepalive_permit_without_calls", 1),
]


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------


def build_servers(
    hv_id: str = "hv_01",
    my_address: str = "localhost",
    my_port: int = 50052,
    my_proxy_port: int = 50053,
    capacity: int = 32,
    workers: int = 10,
    gestor_address: str = "localhost:50051",
) -> tuple[grpc.Server, grpc.Server, Hypervisor, GestorClient]:
    """
    Construye y devuelve:
        (servidor_gestion, servidor_proxy, hypervisor, gestor_client)

    No arranca los servidores; solo los configura.
    Separar construcción de arranque permite tests de integración sin procesos.
    """
    # 1. Cliente hacia el Gestor
    gestor_client = GestorClient(gestor_address)

    # 2. Lógica pura
    hv = Hypervisor(
        hypervisor_id=hv_id,
        gestor_client=gestor_client,
        capacity=capacity,
        my_address=my_address,
        my_port=my_port,
        my_proxy_port=my_proxy_port,
    )

    # 3. Servidor de gestión (Gestor → HV)
    management_server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=workers),
        options=_GRPC_OPTIONS,
    )
    hypervisor_service_pb2_grpc.add_HypervisorServiceServicer_to_server(
        HypervisorServicer(hv), management_server
    )
    management_server.add_insecure_port(f"[::]:{my_port}")

    # 4. Servidor proxy (Bot → HV)
    proxy_server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=workers),
        options=_GRPC_OPTIONS,
    )
    world_proxy_service_pb2_grpc.add_WorldProxyServiceServicer_to_server(
        WorldProxyServicer(hv), proxy_server
    )
    proxy_server.add_insecure_port(f"[::]:{my_proxy_port}")

    return management_server, proxy_server, hv, gestor_client


# ---------------------------------------------------------------------------
# Arranque principal
# ---------------------------------------------------------------------------


def serve():

    setup_remote_logging(
        mundo_address="10.0.0.1:50060",  # IP local del Mundo
        component="gestor",
        local_log_path="logs/gestor_local.log",
    )

    hv_id = os.environ.get("HV_ID", "hv_01")
    my_address = os.environ.get("HV_ADDRESS", "localhost")
    my_port = int(os.environ.get("HV_PORT", "50052"))
    my_proxy_port = int(os.environ.get("HV_PROXY_PORT", "50053"))
    capacity = int(os.environ.get("HV_CAPACITY", "32"))
    workers = int(os.environ.get("HV_WORKERS", "10"))
    gestor_addr = os.environ.get("GESTOR_ADDRESS", "localhost:50051")

    management_server, proxy_server, hv, gestor_client = build_servers(
        hv_id=hv_id,
        my_address=my_address,
        my_port=my_port,
        my_proxy_port=my_proxy_port,
        capacity=capacity,
        workers=workers,
        gestor_address=gestor_addr,
    )

    # Arrancamos los dos servidores
    management_server.start()
    logger.info(
        "HypervisorService arrancado en [::]:%d  (gestión, Gestor → HV)",
        my_port,
    )

    proxy_server.start()
    logger.info(
        "WorldProxyService arrancado en [::]:%d  (proxy, Bot → HV)",
        my_proxy_port,
    )

    # Nos registramos en el Gestor (con reintentos por si arranca antes)
    _register_with_retries(hv, retries=10, delay=2.0)

    # Heartbeat periódico: reportamos carga cada 30 s
    import threading

    def _heartbeat():
        while True:
            time.sleep(30)
            try:
                hv.report_load()
            except Exception as exc:
                logger.warning("Heartbeat fallido: %s", exc)

    threading.Thread(target=_heartbeat, daemon=True, name="hv-heartbeat").start()

    # Apagado limpio
    stop_event = {"fired": False}

    def _shutdown(signum, frame):
        if stop_event["fired"]:
            return
        stop_event["fired"] = True
        logger.info("Señal %d — apagando Hypervisor %s...", signum, hv_id)
        management_server.stop(grace=5)
        proxy_server.stop(grace=5)
        gestor_client.close()
        logger.info("Hypervisor %s apagado.", hv_id)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        _shutdown(signal.SIGINT, None)


def _register_with_retries(hv: Hypervisor, retries: int = 10, delay: float = 2.0):
    """
    Intenta registrarse en el Gestor hasta `retries` veces.
    Espera `delay` segundos entre intentos.
    El Gestor puede tardar en arrancar si los procesos se lanzan juntos.
    """
    for attempt in range(1, retries + 1):
        try:
            ok = hv.register_with_gestor()
            if ok:
                return
            logger.warning(
                "Registro rechazado por el Gestor (intento %d/%d). Reintentando...",
                attempt,
                retries,
            )
        except Exception as exc:
            logger.warning(
                "No se pudo contactar con el Gestor (intento %d/%d): %s",
                attempt,
                retries,
                exc,
            )
        time.sleep(delay)

    logger.error(
        "No se pudo registrar en el Gestor tras %d intentos. "
        "El Hypervisor sigue en marcha pero sin asignación de bots.",
        retries,
    )


if __name__ == "__main__":
    serve()
