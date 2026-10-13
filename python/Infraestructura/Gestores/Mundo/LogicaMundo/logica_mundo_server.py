# Infraestructura/Gestores/Mundo/LogicaMundo/logica_mundo_server.py
"""
Arranca el servidor gRPC de LogicaMundo. Al arrancar NO puebla el mundo:
- Arranque limpio: el cliente (Gestor/consola) llama al RPC GenerarMundo y
  sondea EstadoGeneracionMundo hasta COMPLETADA.
- Arranque desde snapshot: se llama al RPC LoadState.
Este proceso solo se queda escuchando hasta recibir una señal de apagado.
"""

from __future__ import annotations

import asyncio
import logging
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
from Infraestructura.Gestores.Mundo.LogicaMundo.logica_mundo import LogicaMundo
from Infraestructura.Gestores.Mundo.LogicaMundo.logica_mundo_servicer import (
    LogicaMundoServicer,
)
from Infraestructura.Gestores.Log.local_logging import setup_local_logging
from Infraestructura.Gestores.Log.buffered_log_handler import setup_buffered_logging
from Infraestructura.Gestores.Log.log_pull_servicer import LogPullServicerAsync
from Utils.Sistema.sistema import registrar_signals
from Config.settings import (
    GESTOR_BOTS_ADDRESS,
    LOG_LEVEL,
    LOGICA_MUNDO_HOST,
    LOGICA_MUNDO_PORT,
    MODO,
    LOG_DIR,
)

logger = logging.getLogger("logica_mundo_server")

_COMPONENT_ID = "logica_mundo"


async def serve() -> None:
    host = LOGICA_MUNDO_HOST
    port = LOGICA_MUNDO_PORT
    gestor_bots_address = GESTOR_BOTS_ADDRESS
    log_level = getattr(logging, LOG_LEVEL)

    if MODO == "local":
        setup_local_logging(component=_COMPONENT_ID, log_dir=LOG_DIR, level=log_level)
    else:
        log_handler = setup_buffered_logging(component=_COMPONENT_ID, level=log_level)

    # Cliente hacia Gestor_Bots — usado solo por LogicaMundo.matar_bot()
    # para notificar la muerte de un bot decidida por la lógica del
    # mundo (ver logicaMundo.py). Async porque Logica_Mundo es
    # enteramente asyncio.
    from Infraestructura.Gestores.Transporte.gestor_bots_client_async import (
        GestorBotsClientAsync,
    )

    gestor_bots_client = GestorBotsClientAsync(gestor_bots_address)

    logica = LogicaMundo(gestor_bots_client=gestor_bots_client)
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
    logger.info("Apagando Logica_Mundo...")
    await logica.apagar()  # cancela la generación del mundo si está en curso
    await server.stop(grace=5)  # deja terminar los RPC en vuelo (p. ej. MatarBot)
    await gestor_bots_client.close()  # DESPUÉS de stop: esos RPC aún lo usan
    logger.info("Logica_Mundo apagado.")


def main() -> None:
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
