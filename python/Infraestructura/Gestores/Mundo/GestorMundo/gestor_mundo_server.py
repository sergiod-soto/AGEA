# Infraestructura/Gestores/Mundo/GestorMundo/gestor_mundo_server.py
"""
gestor_mundo_server.py

CORREGIDO: GestorMundo() se instanciaba sin el parámetro logica_client
obligatorio (TypeError garantizado en cualquier modo de arranque).
Se construye aquí un LogicaMundoClient a partir de LOGICA_MUNDO_ADDRESS
— mismo patrón que ya usan gestor_bots_server.py y
comunicaciones_remoto_server.py para conectar con Logica_Mundo — y se
cierra en el shutdown junto con el servidor gRPC.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).parents[4]))

from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import (
    log_pull_service_pb2_grpc,
)
from Infraestructura.Gestores.Transporte.logica_mundo_client import LogicaMundoClient
from Config.settings import (
    FRESH,
    GESTOR_MUNDO_HOST,
    GESTOR_MUNDO_PORT,
    LOG_LEVEL,
    LOGICA_MUNDO_ADDRESS,
    MODO,
    LOG_DIR,
)
from Utils.Sistema.sistema import registrar_signals
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import (
    ErrorFatal,
    GestorMundo,
)
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo_servicer import (
    GestorMundoServicer,
)
from Infraestructura.Gestores.Log.local_logging import setup_local_logging
from Infraestructura.Gestores.Log.buffered_log_handler import setup_buffered_logging
from Infraestructura.Gestores.Log.log_pull_servicer import LogPullServicerAsync

logger = logging.getLogger(__name__)


# Nombre fijo: ya registrado en log_categorias._CARPETA_POR_COMPONENTE
# como "mundo" → carpeta Logs/Mundo/. En modo remoto, gestor_mundo corre
# en su propia instancia EC2 (ver remote.py) igual que los demás
# componentes, así que necesita el mismo tratamiento de logging pull.
_COMPONENT_ID = "mundo"


async def serve(fresh: bool, log_level: int) -> int:
    """
    Arranca el GestorMundo y lo mantiene vivo. Devuelve el código de salida del
    proceso: 0 = apagado ordenado (señal), 1 = error fatal o bucle de ticks
    muerto. No hay reintento: un fallo de sincronización deja los Sectores y
    Logica divergiendo, así que el proceso debe morir.
    """
    # Logging: única fuente de verdad para el logger raíz.
    if MODO == "local":
        setup_local_logging(component=_COMPONENT_ID, log_dir=LOG_DIR, level=log_level)
    else:
        log_handler = setup_buffered_logging(component=_COMPONENT_ID, level=log_level)

    # Cliente hacia Logica_Mundo: conexión perezosa, dirección por env var.
    logica_client = LogicaMundoClient(LOGICA_MUNDO_ADDRESS)
    gestor = GestorMundo(logica_client=logica_client)
    servicer = GestorMundoServicer(gestor)

    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", -1),
            ("grpc.max_receive_message_length", -1),
        ]
    )
    pb_grpc.add_GestorMundoServiceServicer_to_server(servicer, server)

    if MODO != "local":
        # Mismo servidor y puerto: no se abre ningún puerto adicional para logs.
        log_pull_service_pb2_grpc.add_LogPullServiceServicer_to_server(
            LogPullServicerAsync(log_handler), server
        )

    address = f"{GESTOR_MUNDO_HOST}:{GESTOR_MUNDO_PORT}"
    server.add_insecure_port(address)
    await server.start()
    logger.info("GestorMundo gRPC escuchando en %s", address)

    codigo_salida = 0
    tareas: list[asyncio.Task] = []
    try:
        await gestor.start(fresh=fresh)

        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        def _shutdown(sig):
            logger.info("Señal %s recibida — apagando...", sig.name)
            loop.call_soon_threadsafe(stop_event.set)

        registrar_signals(loop, _shutdown)

        # run_loop se lanza SIN envoltorio de reintento: cualquier excepción
        # (incluida ErrorFatal) mata la tarea y, con ella, el proceso.
        tick_task = asyncio.create_task(gestor.run_loop(), name="tick_loop")
        stop_task = asyncio.create_task(stop_event.wait(), name="stop_wait")
        fatal_task = asyncio.create_task(gestor.fatal_event.wait(), name="fatal_wait")
        tareas = [tick_task, stop_task, fatal_task]

        # Lo primero que ocurra: señal de apagado, fatal escalado (resume(),
        # tareas de fondo) o muerte del bucle de ticks.
        await asyncio.wait(tareas, return_when=asyncio.FIRST_COMPLETED)

        if not stop_task.done():
            codigo_salida = 1
            if tick_task.done() and not tick_task.cancelled():
                exc = tick_task.exception()
                logger.critical("El bucle de ticks murió: %r", exc, exc_info=exc)
            else:
                logger.critical("Error fatal escalado: %r", gestor.error_fatal)
    except ErrorFatal:
        # Fatal durante el arranque (p. ej. ErrorCargaSector en start()).
        logger.critical("Arranque abortado por error fatal.", exc_info=True)
        codigo_salida = 1
    finally:
        logger.info("Deteniendo bucle de ticks...")
        for t in tareas:
            t.cancel()
        await asyncio.gather(*tareas, return_exceptions=True)

        logger.info("Apagando servidor gRPC...")
        await server.stop(grace=5)
        await gestor.close()  # canales a sectores y a Gestor_Bots
        await logica_client.close()

    logger.info("GestorMundo detenido (código %d).", codigo_salida)
    return codigo_salida


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level",
        default=LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()
    log_level = getattr(logging, args.log_level)

    try:
        codigo = asyncio.run(serve(fresh=FRESH, log_level=log_level))
    except KeyboardInterrupt:
        codigo = 0
    sys.exit(codigo)


if __name__ == "__main__":
    main()
