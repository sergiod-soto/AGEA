"""
Envía logs al Mundo (local) desde componentes remotos (AWS).

No se usa directamente: RemoteLogHandler
lo instancia y lo llama en background. El código de aplicación
solo configura el handler y usa logging normalmente.

Uso directo (tests o casos especiales):
    client = LogClient("mundo_host:50060", component="hv_01")
    client.send("hola desde el hypervisor", level=logging.INFO)
    client.close()
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import grpc

from Gestores.Transporte.Proto_Generated import (
    log_service_pb2,
    log_service_pb2_grpc,
)

# Mapeado logging Python → LogLevel protobuf
_PY_TO_PB: dict[int, int] = {
    logging.DEBUG:    log_service_pb2.DEBUG,
    logging.INFO:     log_service_pb2.INFO,
    logging.WARNING:  log_service_pb2.WARNING,
    logging.ERROR:    log_service_pb2.ERROR,
    logging.CRITICAL: log_service_pb2.CRITICAL,
}


class LogClient:
    """
    Cliente gRPC del LogService.

    Parámetros
    ----------
    address : str
        "host:puerto" del LogServer en el Mundo. Ejemplo: "192.168.1.1:50060"
    component : str
        Nombre del componente ("gestor" | "hv_01" | ...).
        Determina en qué fichero .log se escribirá en el Mundo.
    timeout : float
        Timeout por RPC (default 5 s; los logs no deben bloquear).
    """

    def __init__(
        self,
        address: str,
        component: str,
        timeout: float = 5.0,
    ):
        self._address   = address
        self._component = component
        self._timeout   = timeout

        self._channel = grpc.insecure_channel(
            address,
            options=[
                ("grpc.max_receive_message_length", 16 * 1024 * 1024),
                # Reconexión automática si el Mundo se reinicia
                ("grpc.enable_retries", 1),
            ],
        )
        self._stub = log_service_pb2_grpc.LogServiceStub(self._channel)

    def close(self) -> None:
        self._channel.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # Envío
    # ------------------------------------------------------------------

    def send(
        self,
        message: str,
        level: int = logging.INFO,
        logger_name: str = "",
        exc_info: str = "",
        timestamp_ms: Optional[int] = None,
    ) -> bool:
        """
        Envía un único log al Mundo. Devuelve True si llegó bien.
        En caso de error de red, devuelve False silenciosamente
        (los logs no deben romper el flujo principal).
        """
        record = self._make_record(message, level, logger_name,
                                   exc_info, timestamp_ms)
        try:
            self._stub.SendLog(record, timeout=self._timeout)
            return True
        except grpc.RpcError:
            return False

    def send_batch(self, records: list[log_service_pb2.LogRecord]) -> bool:
        """
        Envía un lote de LogRecord de una sola vez.
        Usado por RemoteLogHandler para vaciar la cola en background.
        """
        if not records:
            return True
        batch = log_service_pb2.LogBatch(records=records)
        try:
            self._stub.SendBatch(batch, timeout=self._timeout)
            return True
        except grpc.RpcError:
            return False

    def make_record(
        self,
        message: str,
        level: int,
        logger_name: str = "",
        exc_info: str = "",
        timestamp_ms: Optional[int] = None,
    ) -> log_service_pb2.LogRecord:
        """
        Construye un LogRecord protobuf. Público para que
        RemoteLogHandler lo use sin duplicar lógica.
        """
        return self._make_record(message, level, logger_name,
                                 exc_info, timestamp_ms)

    def _make_record(
        self,
        message: str,
        level: int,
        logger_name: str,
        exc_info: str,
        timestamp_ms: Optional[int],
    ) -> log_service_pb2.LogRecord:
        return log_service_pb2.LogRecord(
            component=self._component,
            level=_PY_TO_PB.get(level, log_service_pb2.INFO),
            logger=logger_name,
            message=message,
            timestamp=timestamp_ms or int(time.time() * 1000),
            exc_info=exc_info,
        )
