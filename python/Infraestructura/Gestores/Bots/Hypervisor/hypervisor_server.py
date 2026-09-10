# Infraestructura/Gestores/Bots/Hypervisor/hypervisor_server.py
"""
hypervisor_server.py

Migrado a asyncio junto con el resto de Hypervisor. Cambios de fondo:
  - grpc.server(ThreadPoolExecutor) -> grpc.aio.server() (se mantienen
    los dos servidores separados de siempre: management_server y
    proxy_server, ahora ambos corriendo en el mismo loop de eventos).
  - GestorBotsClient (síncrono) -> GestorBotsClientAsync — cambio
    confirmado junto con el resto de la migración.
  - El registro con reintentos y el heartbeat periódico (antes
    threading.Thread + time.sleep bloqueante) pasan a ser corutinas /
    asyncio.Task con asyncio.sleep.
  - El apagado por señal usa el mismo patrón que el resto de
    *_server.py (registrar_signals + stop_event), en vez de
    signal.signal directo + sys.exit.

Se mantiene build_servers() como función aparte (igual que en la
versión síncrona) para poder construir los servidores sin arrancar el
bucle completo, por si algo más (tests) lo necesita.
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
    hypervisor_service_pb2_grpc,
    world_proxy_service_pb2_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import (
    log_pull_service_pb2_grpc,
)
from Infraestructura.Gestores.Transporte.gestor_bots_client_async import (
    GestorBotsClientAsync,
)
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor_servicer import (
    HypervisorServicer,
)
from Infraestructura.Gestores.Bots.Hypervisor.world_proxy_servicer import (
    WorldProxyServicer,
)
from Infraestructura.Gestores.Log.local_logging import setup_local_logging
from Infraestructura.Gestores.Log.buffered_log_handler import setup_buffered_logging
from Infraestructura.Gestores.Log.log_pull_servicer import LogPullServicerAsync
from Utils.Sistema.sistema import registrar_signals
from Config.settings import (
    GESTOR_BOTS_ADDRESS,
    HYPERVISOR_CAPACITY,
    HYPERVISOR_HOST,
    HYPERVISOR_ID,
    HYPERVISOR_PORT,
    HYPERVISOR_PROXY_PORT,
    LOG_LEVEL,
    MODO,
    LOG_DIR,
)

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
    gestor_address: str,
) -> tuple[grpc.aio.Server, grpc.aio.Server, Hypervisor, GestorBotsClientAsync]:
    gestor_client = GestorBotsClientAsync(gestor_address)
    hv = Hypervisor(
        hypervisor_id=hv_id,
        gestor_client=gestor_client,
        capacity=capacity,
        my_address=my_address,
        my_port=my_port,
        my_proxy_port=my_proxy_port,
    )

    management_server = grpc.aio.server(options=_GRPC_OPTIONS)
    hypervisor_service_pb2_grpc.add_HypervisorServiceServicer_to_server(
        HypervisorServicer(hv), management_server
    )
    management_server.add_insecure_port(f"[::]:{my_port}")

    proxy_server = grpc.aio.server(options=_GRPC_OPTIONS)
    world_proxy_service_pb2_grpc.add_WorldProxyServiceServicer_to_server(
        WorldProxyServicer(hv), proxy_server
    )
    proxy_server.add_insecure_port(f"[::]:{my_proxy_port}")

    return management_server, proxy_server, hv, gestor_client


async def _register_with_retries(
    hv: Hypervisor, retries: int = 10, delay: float = 2.0
) -> None:
    for attempt in range(1, retries + 1):
        try:
            if await hv.register_with_gestor():
                return
            logger.warning("Registro rechazado (intento %d/%d).", attempt, retries)
        except Exception as exc:
            logger.warning(
                "No se pudo contactar con Gestor (intento %d/%d): %s",
                attempt,
                retries,
                exc,
            )
        await asyncio.sleep(delay)
    logger.error("No se pudo registrar tras %d intentos.", retries)


async def _heartbeat_loop(hv: Hypervisor) -> None:
    while True:
        await asyncio.sleep(30)
        try:
            await hv.report_load()
        except Exception as exc:
            logger.warning("Heartbeat fallido: %s", exc)


async def serve() -> None:
    hv_id = HYPERVISOR_ID
    my_address = HYPERVISOR_HOST
    my_port = HYPERVISOR_PORT
    my_proxy_port = HYPERVISOR_PROXY_PORT
    capacity = HYPERVISOR_CAPACITY
    gestor_address = GESTOR_BOTS_ADDRESS
    log_level = getattr(logging, LOG_LEVEL.upper())

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
        gestor_address=gestor_address,
    )

    if MODO != "local":
        log_pull_service_pb2_grpc.add_LogPullServiceServicer_to_server(
            LogPullServicerAsync(log_handler), management_server
        )

    await management_server.start()
    logger.info("HypervisorService arrancado en [::]:%d", my_port)

    await proxy_server.start()
    logger.info("WorldProxyService arrancado en [::]:%d", my_proxy_port)

    await _register_with_retries(hv)

    heartbeat_task = asyncio.create_task(_heartbeat_loop(hv), name="hv-heartbeat")

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig):
        logger.info("Señal %s — apagando Hypervisor %s...", sig.name, hv_id)
        loop.call_soon_threadsafe(stop_event.set)

    registrar_signals(loop, _shutdown)

    await stop_event.wait()

    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass

    logger.info("Apagando servidores gRPC de Hypervisor %s...", hv_id)
    await management_server.stop(grace=5)
    await proxy_server.stop(grace=5)
    await gestor_client.close()
    logger.info("Hypervisor %s apagado.", hv_id)


def main() -> None:
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
