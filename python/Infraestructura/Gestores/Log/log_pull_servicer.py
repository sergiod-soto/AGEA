# Infraestructura/Gestores/Log/log_pull_servicer.py
"""
log_pull_servicer.py — Lado servidor del RPC PullLogs.

Se registra en el mismo servidor gRPC que el servicio principal de cada
componente (mismo puerto, sin abrir uno nuevo). Hay DOS variantes porque
el proyecto mezcla servidores síncronos y asíncronos de gRPC:

  - Sector, Gestor_Bots y Gestor_Mundo usan grpc.aio.server() → sus
    servicers son async def (ver Gestor_Bots_Servicer, GestorMundoServicer).
  - Hypervisor usa grpc.server() con ThreadPoolExecutor (síncrono) → su
    servicer usa def normal (ver HypervisorServicer).

Registrar la variante equivocada en el servidor equivocado no falla al
importar — falla en tiempo de ejecución de forma confusa, porque un
servidor síncrono no sabe "esperar" una coroutine.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import (
    log_pull_service_pb2_grpc,
    log_service_pb2,
)
from Infraestructura.Gestores.Log.buffered_log_handler import BufferedLogHandler


class LogPullServicer(log_pull_service_pb2_grpc.LogPullServiceServicer):
    """Variante síncrona — usar con grpc.server() (Hypervisor)."""

    def __init__(self, handler: BufferedLogHandler):
        self._handler = handler

    def PullLogs(self, request, context):
        registros = self._handler.drain()
        return log_service_pb2.LogBatch(records=registros)


class LogPullServicerAsync(log_pull_service_pb2_grpc.LogPullServiceServicer):
    """
    Variante asíncrona — usar con grpc.aio.server() (Sector, Gestor_Bots,
    Gestor_Mundo). drain() en sí es síncrono (solo bloquea sobre un lock
    en memoria, es instantáneo), pero el método RPC debe ser async def
    para que el servidor aio lo despache correctamente.
    """

    def __init__(self, handler: BufferedLogHandler):
        self._handler = handler

    async def PullLogs(self, request, context):
        registros = self._handler.drain()
        return log_service_pb2.LogBatch(records=registros)
