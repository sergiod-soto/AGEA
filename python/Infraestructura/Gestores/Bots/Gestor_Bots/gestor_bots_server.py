# Infraestructura/Gestores/Bots/Gestor_Bots/gestor_bots_server.py
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

from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import (
    log_pull_service_pb2_grpc,
)
from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots_servicer import (
    Gestor_Bots_Servicer,
)
from Infraestructura.Gestores.Log.local_logging import setup_local_logging
from Infraestructura.Gestores.Log.buffered_log_handler import setup_buffered_logging
from Infraestructura.Gestores.Log.log_pull_servicer import LogPullServicerAsync
from Utils.Sistema.sistema import registrar_signals
from Config.settings import MODO, LOG_DIR

logger = logging.getLogger("gestor_bots_server")

# Único componente de este tipo — nombre fijo, ya registrado en
# log_categorias._CARPETA_POR_COMPONENTE.
_COMPONENT_ID = "gestor_bots"


async def serve() -> None:
    host = os.getenv("GESTOR_BOTS_HOST", "[::]")
    port = int(os.getenv("GESTOR_BOTS_PORT", 50051))
    workers = int(os.getenv("GESTOR_BOTS_WORKERS", 10))
    bots_por_hv = int(os.getenv("BOTS_POR_HYPERVISOR", 100))
    # Antes: GESTOR_MUNDO_ADDRESS / GestorMundoClient. Las acciones de
    # bots y el resto de operaciones sobre estado ahora se resuelven
    # contra Logica_Mundo directamente (ver gestor_bots.py).
    logica_mundo_address = os.getenv("LOGICA_MUNDO_ADDRESS", "localhost:50250")
    log_level_name = os.getenv("LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_name)

    if MODO == "local":
        setup_local_logging(component=_COMPONENT_ID, log_dir=LOG_DIR, level=log_level)
    else:
        log_handler = setup_buffered_logging(component=_COMPONENT_ID, level=log_level)

    address = f"{host}:{port}"

    logger.info(
        "Configuración — host=%s workers=%d bots_por_hv=%d",
        address,
        workers,
        bots_por_hv,
    )

    try:
        from Infraestructura.Gestores.Transporte.hypervisor_client import (
            HypervisorClient,
        )

        def hypervisor_client_factory(addr: str, port: int) -> HypervisorClient:
            return HypervisorClient(addr, port)

    except ImportError:
        logger.warning("HypervisorClient no disponible.")
        hypervisor_client_factory = None

    from Infraestructura.Gestores.Transporte.logica_mundo_client import (
        LogicaMundoClient,
    )

    logica_client = LogicaMundoClient(logica_mundo_address)

    gestor = Gestor_Bots(
        logica_client=logica_client,
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

    if MODO != "local":
        log_pull_service_pb2_grpc.add_LogPullServiceServicer_to_server(
            LogPullServicerAsync(log_handler), server
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
    await logica_client.close()
    await server.stop(grace=5)
    logger.info("Gestor_Bots apagado.")


def main() -> None:
    # Sin logging.basicConfig() aquí: serve() configura el logger raíz vía
    # setup_local_logging/setup_buffered_logging (ver comentario equivalente
    # en sector_server.py sobre por qué basicConfig() interfería).
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
