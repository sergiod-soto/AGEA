# Infraestructura/Gestores/Mundo/Logica_Mundo/logica_mundo_server.py
"""
logica_mundo_server.py

poblar_suelo=FRESH (NUEVO): LogicaMundo no sabe nada de FRESH/snapshots
—recibe el flag explícito de quien lo instancia, que es este fichero.
Si es un arranque en frío (FRESH=true), se puebla el suelo aquí mismo
al construir LogicaMundo. Si no (se espera restaurar desde un
snapshot), no se puebla: quien orqueste el resume es responsable de
llamar al RPC LoadState después de que este proceso arranque — ese
snapshot ya trae su propio suelo guardado, así que poblarlo aquí sería
trabajo tirado (se sobreescribiría igualmente al cargar el snapshot).
Este fichero no contiene ninguna llamada a load_state() — si la
restauración no llega a ocurrir por lo que sea, el mundo se quedaría
sin ningún Suelo; es el mismo riesgo que ya existía para cualquier
otro elemento antes de este cambio, no algo nuevo que introduzca esto.
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
    logica_mundo_service_pb2_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import (
    log_pull_service_pb2_grpc,
)
from Infraestructura.Gestores.Mundo.Logica_Mundo.logica_mundo import LogicaMundo
from Infraestructura.Gestores.Mundo.Logica_Mundo.logica_mundo_servicer import (
    LogicaMundoServicer,
)
from Infraestructura.Gestores.Log.local_logging import setup_local_logging
from Infraestructura.Gestores.Log.buffered_log_handler import setup_buffered_logging
from Infraestructura.Gestores.Log.log_pull_servicer import LogPullServicerAsync
from Utils.Sistema.sistema import registrar_signals
from Config.settings import MODO, LOG_DIR, FRESH

logger = logging.getLogger("logica_mundo_server")

_COMPONENT_ID = "logica_mundo"


async def serve() -> None:
    host = os.getenv("LOGICA_MUNDO_HOST", "[::]")
    port = int(os.getenv("LOGICA_MUNDO_PORT", 50250))
    gestor_bots_address = os.getenv("GESTOR_BOTS_ADDRESS", "localhost:50051")
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))

    if MODO == "local":
        setup_local_logging(component=_COMPONENT_ID, log_dir=LOG_DIR, level=log_level)
    else:
        log_handler = setup_buffered_logging(component=_COMPONENT_ID, level=log_level)

    # Cliente hacia Gestor_Bots — usado solo por LogicaMundo.matar_bot()
    # para notificar la muerte de un bot decidida por la lógica del
    # mundo (ver logica_mundo.py). Async porque Logica_Mundo es
    # enteramente asyncio.
    from Infraestructura.Gestores.Transporte.gestor_bots_client_async import (
        GestorBotsClientAsync,
    )

    gestor_bots_client = GestorBotsClientAsync(gestor_bots_address)

    # poblar_suelo=FRESH: ver docstring del módulo — solo se puebla el
    # suelo aquí si es un arranque en frío; si se va a restaurar un
    # snapshot, ese snapshot ya trae el suelo consigo.
    logica = LogicaMundo(gestor_bots_client=gestor_bots_client, poblar_suelo=FRESH)
    servicer = LogicaMundoServicer(logica)

    server = grpc.aio.server(
        options=[
            ("grpc.max_receive_message_length", 256 * 1024 * 1024),
            ("grpc.max_send_message_length", 256 * 1024 * 1024),
            ("grpc.keepalive_time_ms", 20_000),
            ("grpc.keepalive_timeout_ms", 10_000),
        ],
    )
    logica_mundo_service_pb2_grpc.add_LogicaMundoServiceServicer_to_server(
        servicer, server
    )

    if MODO != "local":
        log_pull_service_pb2_grpc.add_LogPullServiceServicer_to_server(
            LogPullServicerAsync(log_handler), server
        )

    address = f"{host}:{port}"
    server.add_insecure_port(address)
    await server.start()
    logger.info("Logica_Mundo escuchando en %s", address)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig):
        logger.info("Señal %s — apagando Logica_Mundo...", sig.name)
        loop.call_soon_threadsafe(stop_event.set)

    registrar_signals(loop, _shutdown)

    await stop_event.wait()
    await gestor_bots_client.close()
    await server.stop(grace=5)
    logger.info("Logica_Mundo apagado.")


def main() -> None:
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
