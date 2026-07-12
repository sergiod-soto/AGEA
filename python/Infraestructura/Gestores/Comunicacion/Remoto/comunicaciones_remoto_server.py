# Infraestructura/Gestores/Comunicacion/Remoto/comunicaciones_remoto_server.py
"""
comunicaciones_remoto_server.py — Arranque del proceso
Comunicaciones_Remoto.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).parents[4]))

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    comunicacion_remota_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import (
    log_pull_service_pb2_grpc,
)
from Infraestructura.Gestores.Comunicacion.Remoto.clientes_remotos import (
    ClientesRemotos,
)
from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto import (
    ComunicacionesRemoto,
)
from Infraestructura.Gestores.Comunicacion.Remoto.comunicaciones_remoto_servicer import (
    ComunicacionesRemotoServicer,
)
from Infraestructura.Gestores.Transporte.logica_mundo_client import LogicaMundoClient
from Infraestructura.Gestores.Transporte.gestor_mundo_client import GestorMundoClient
from Infraestructura.Gestores.Transporte.gestor_bots_client_async import (
    GestorBotsClientAsync,
)
from Infraestructura.Gestores.Log.local_logging import setup_local_logging
from Infraestructura.Gestores.Log.buffered_log_handler import setup_buffered_logging
from Infraestructura.Gestores.Log.log_pull_servicer import LogPullServicerAsync
from Utils.Sistema.sistema import registrar_signals
from Config.settings import MODO, LOG_DIR

logger = logging.getLogger("comunicaciones_remoto_server")

_COMPONENT_ID = "comunicaciones_remoto"


async def serve() -> None:
    host = os.getenv("COMUNICACIONES_REMOTO_HOST", "[::]")
    port = int(os.getenv("COMUNICACIONES_REMOTO_PORT", 50500))
    logica_mundo_address = os.getenv("LOGICA_MUNDO_ADDRESS", "localhost:50250")
    gestor_mundo_address = os.getenv("GESTOR_MUNDO_ADDRESS", "localhost:50200")
    gestor_bots_address = os.getenv("GESTOR_BOTS_ADDRESS", "localhost:50051")
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))

    if MODO == "local":
        setup_local_logging(component=_COMPONENT_ID, log_dir=LOG_DIR, level=log_level)
    else:
        log_handler = setup_buffered_logging(component=_COMPONENT_ID, level=log_level)

    clientes = ClientesRemotos(
        logica_mundo=LogicaMundoClient(logica_mundo_address),
        gestor_mundo=GestorMundoClient(gestor_mundo_address),
        gestor_bots=GestorBotsClientAsync(gestor_bots_address),
    )
    logica = ComunicacionesRemoto(clientes)
    servicer = ComunicacionesRemotoServicer(logica)

    server = grpc.aio.server(
        options=[
            ("grpc.max_receive_message_length", 256 * 1024 * 1024),
            ("grpc.max_send_message_length", 256 * 1024 * 1024),
        ]
    )
    pb_grpc.add_ComunicacionRemotaServiceServicer_to_server(servicer, server)

    if MODO != "local":
        log_pull_service_pb2_grpc.add_LogPullServiceServicer_to_server(
            LogPullServicerAsync(log_handler), server
        )

    address = f"{host}:{port}"
    server.add_insecure_port(address)
    await server.start()
    logger.info("Comunicaciones_Remoto escuchando en %s", address)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig):
        logger.info("Señal %s — apagando Comunicaciones_Remoto...", sig.name)
        loop.call_soon_threadsafe(stop_event.set)

    registrar_signals(loop, _shutdown)

    await stop_event.wait()
    await clientes.close()
    await server.stop(grace=5)
    logger.info("Comunicaciones_Remoto apagado.")


def main() -> None:
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
