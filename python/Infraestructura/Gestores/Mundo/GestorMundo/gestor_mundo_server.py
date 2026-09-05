# Infraestructura/Gestores/Mundo/Gestor_Mundo/gestor_mundo_server.py
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
from Config.settings import FRESH, MODO, LOG_DIR
from Utils.Sistema.sistema import registrar_signals
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import GestorMundo
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo_servicer import (
    GestorMundoServicer,
)
from Infraestructura.Gestores.Log.local_logging import setup_local_logging
from Infraestructura.Gestores.Log.buffered_log_handler import setup_buffered_logging
from Infraestructura.Gestores.Log.log_pull_servicer import LogPullServicerAsync

logger = logging.getLogger(__name__)

GESTOR_MUNDO_HOST = os.getenv("GESTOR_MUNDO_HOST", "[::]")
GESTOR_MUNDO_PORT = int(os.getenv("GESTOR_MUNDO_PORT", 50200))
GESTOR_MUNDO_WORKERS = int(os.getenv("GESTOR_MUNDO_WORKERS", 10))

# Nombre fijo: ya registrado en log_categorias._CARPETA_POR_COMPONENTE
# como "mundo" → carpeta Logs/Mundo/. En modo remoto, gestor_mundo corre
# en su propia instancia EC2 (ver remote.py) igual que los demás
# componentes, así que necesita el mismo tratamiento de logging pull.
_COMPONENT_ID = "mundo"


async def serve(fresh: bool, log_level: int) -> None:
    # Logging: única fuente de verdad para el logger raíz (sin
    # logging.basicConfig() en paralelo — ver mismo razonamiento en
    # sector_server.py / gestor_bots_server.py / hypervisor_server.py).
    if MODO == "local":
        setup_local_logging(component=_COMPONENT_ID, log_dir=LOG_DIR, level=log_level)
    else:
        log_handler = setup_buffered_logging(component=_COMPONENT_ID, level=log_level)

    # Cliente hacia Logica_Mundo — GestorMundo lo necesita para TODA su
    # lógica de estado desde el refactor (obtener_celdas_en_region,
    # actualizar_celdas, avanzar_elementos_globales, save_snapshot,
    # load_state — ver gestor_mundo.py). Mismo patrón que
    # gestor_bots_server.py/comunicaciones_remoto_server.py: dirección
    # vía env var, conexión perezosa (el propio cliente no abre canal
    # hasta la primera llamada).
    logica_mundo_address = os.getenv("LOGICA_MUNDO_ADDRESS", "localhost:50250")
    logica_client = LogicaMundoClient(logica_mundo_address)

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
        # Mismo servidor y puerto que GestorMundoService — no se abre
        # ningún puerto adicional para logs.
        log_pull_service_pb2_grpc.add_LogPullServiceServicer_to_server(
            LogPullServicerAsync(log_handler), server
        )

    address = f"{GESTOR_MUNDO_HOST}:{GESTOR_MUNDO_PORT}"
    server.add_insecure_port(address)
    await server.start()
    logger.info("GestorMundo gRPC escuchando en %s", address)

    await gestor.start(fresh=fresh)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig):
        logger.info("Señal %s recibida — apagando...", sig.name)
        loop.call_soon_threadsafe(stop_event.set)

    registrar_signals(loop, _shutdown)

    tick_task = asyncio.create_task(_run_tick_loop(gestor), name="tick_loop")

    await stop_event.wait()

    logger.info("Deteniendo bucle de ticks...")
    tick_task.cancel()
    try:
        await tick_task
    except asyncio.CancelledError:
        pass

    logger.info("Apagando servidor gRPC...")
    await server.stop(grace=5)
    await logica_client.close()
    logger.info("GestorMundo detenido.")


async def _run_tick_loop(gestor: GestorMundo) -> None:
    while True:
        try:
            await gestor.run_loop()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error en bucle de ticks — reintentando en 1s")
            await asyncio.sleep(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()
    log_level = getattr(logging, args.log_level)

    # Sin logging.basicConfig() aquí: serve() configura el logger raíz vía
    # setup_local_logging/setup_buffered_logging. Tenerlos duplicados hacía
    # que basicConfig() añadiera un StreamHandler antes de tiempo, y el
    # guard "if not root.handlers" de esas funciones quedaba siempre en
    # falso — el fichero de log nunca llegaba a añadirse (bug ya cazado).
    try:
        asyncio.run(serve(fresh=FRESH, log_level=log_level))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
