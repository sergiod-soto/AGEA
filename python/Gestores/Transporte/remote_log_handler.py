"""
logging.Handler que intercepta los logs de Python y los envía
al LogService del Mundo (local) de forma asíncrona.

Características:
  - No bloquea el hilo principal: usa una cola + hilo worker.
  - Escribe también en un fichero local en AWS como respaldo
    por si la red cae.
  - Si la cola se llena, descarta logs DEBUG/INFO (nunca ERROR/CRITICAL).
  - Vacía la cola en lotes para reducir llamadas gRPC.

Uso (en gestor_server.py o hypervisor_server.py):
    from Hypervisores.Transporte.remote_log_handler import setup_remote_logging

    # Una línea al arrancar el proceso, antes de cualquier log
    setup_remote_logging(
        mundo_address="192.168.1.1:50060",
        component="hv_01",
        local_log_path="logs/hv_01_local.log",  # respaldo local en AWS
    )

    # A partir de aquí, todos los logs van al Mundo automáticamente
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Hypervisor arrancado")   # → llega a logs/hv_01.log en local
"""

from __future__ import annotations

import logging
import logging.handlers
import queue
import threading
import time
import traceback
from pathlib import Path
from typing import Optional

from Gestores.Transporte.log_client import LogClient
from Gestores.Transporte.Proto_Generated.Otros import log_service_pb2

# Tamaño máximo de la cola en memoria
_QUEUE_MAX = 2000

# Cada cuántos segundos (o registros) se vacía la cola en un batch
_FLUSH_INTERVAL = 2.0   # segundos
_BATCH_SIZE     = 50    # registros por batch


class RemoteLogHandler(logging.Handler):
    """
    Handler de logging que envía registros al LogService del Mundo.

    Flujo:
        logger.info(...) → emit() → cola → hilo worker → LogClient.send_batch()

    El hilo worker corre como daemon y se detiene al llamar close().

    Parámetros
    ----------
    log_client : LogClient
        Cliente ya conectado al LogService del Mundo.
    queue_max : int
        Tamaño máximo de la cola. Cuando se llena, los logs de baja
        prioridad (DEBUG, INFO) se descartan en lugar de bloquear.
    flush_interval : float
        Segundos entre vaciados de la cola (default 2 s).
    batch_size : int
        Máximo de registros por llamada gRPC (default 50).
    """

    def __init__(
        self,
        log_client: LogClient,
        queue_max: int = _QUEUE_MAX,
        flush_interval: float = _FLUSH_INTERVAL,
        batch_size: int = _BATCH_SIZE,
    ):
        super().__init__()
        self._client         = log_client
        self._flush_interval = flush_interval
        self._batch_size     = batch_size
        self._queue: queue.Queue = queue.Queue(maxsize=queue_max)
        self._stop_event     = threading.Event()

        self._worker = threading.Thread(
            target=self._run,
            name=f"remote-log-worker",
            daemon=True,
        )
        self._worker.start()

    # ------------------------------------------------------------------
    # logging.Handler interface
    # ------------------------------------------------------------------

    def emit(self, record: logging.LogRecord) -> None:
        """
        Llamado por el sistema de logging para cada registro.
        Encola el registro sin bloquear.
        """
        try:
            exc_info = ""
            if record.exc_info:
                exc_info = "".join(traceback.format_exception(*record.exc_info))

            pb_record = self._client.make_record(
                message=self.format(record),
                level=record.levelno,
                logger_name=record.name,
                exc_info=exc_info,
                timestamp_ms=int(record.created * 1000),
            )

            # Intentamos encolar sin bloquear
            try:
                self._queue.put_nowait(pb_record)
            except queue.Full:
                # Cola llena: descartamos DEBUG e INFO, guardamos el resto
                if record.levelno >= logging.WARNING:
                    # Hacemos hueco eliminando el registro más antiguo
                    try:
                        self._queue.get_nowait()
                    except queue.Empty:
                        pass
                    self._queue.put_nowait(pb_record)
                # Si es DEBUG/INFO, simplemente se descarta

        except Exception:
            # Nunca propagamos excepciones desde un Handler
            self.handleError(record)

    def close(self) -> None:
        """Para el worker y vacía la cola antes de cerrar."""
        self._stop_event.set()
        self._worker.join(timeout=10.0)
        self._flush()   # vaciado final
        super().close()

    # ------------------------------------------------------------------
    # Worker en background
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """Bucle del hilo worker: vacía la cola cada flush_interval segundos."""
        while not self._stop_event.is_set():
            time.sleep(self._flush_interval)
            self._flush()

    def _flush(self) -> None:
        """Vacía la cola enviando los registros en lotes al Mundo."""
        batch: list[log_service_pb2.LogRecord] = []

        while True:
            try:
                batch.append(self._queue.get_nowait())
                if len(batch) >= self._batch_size:
                    self._client.send_batch(batch)
                    batch = []
            except queue.Empty:
                break

        if batch:
            self._client.send_batch(batch)


# ---------------------------------------------------------------------------
# Función de conveniencia — única llamada necesaria al arrancar
# ---------------------------------------------------------------------------

def setup_remote_logging(
    mundo_address: str,
    component: str,
    local_log_path: Optional[str] = None,
    level: int = logging.DEBUG,
    flush_interval: float = _FLUSH_INTERVAL,
) -> RemoteLogHandler:
    """
    Configura el sistema de logging del proceso para enviar logs al Mundo.

    Añade dos handlers al logger raíz:
      1. RemoteLogHandler  → logs al Mundo via gRPC (asíncrono)
      2. RotatingFileHandler → respaldo local en AWS (síncrono)

    Parámetros
    ----------
    mundo_address : str
        "host:puerto" del LogServer del Mundo. Ejemplo: "10.0.0.1:50060"
    component : str
        Nombre del componente ("gestor" | "hv_01" | "hv_02" ...).
        Determina el fichero .log destino en el Mundo.
    local_log_path : str | None
        Ruta del fichero de respaldo local en AWS.
        Si None, no se crea respaldo local.
        Recomendado: "logs/{component}_local.log"
    level : int
        Nivel mínimo de log (default DEBUG — el Mundo filtra si quiere).
    flush_interval : float
        Segundos entre vaciados de la cola (default 2 s).

    Devuelve el RemoteLogHandler para poder cerrarlo manualmente si es necesario.
    """
    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Handler remoto → Mundo
    client = LogClient(address=mundo_address, component=component)
    remote_handler = RemoteLogHandler(
        log_client=client,
        flush_interval=flush_interval,
    )
    remote_handler.setFormatter(fmt)
    remote_handler.setLevel(level)
    root.addHandler(remote_handler)

    # 2. Handler local → fichero de respaldo en AWS
    if local_log_path:
        Path(local_log_path).parent.mkdir(parents=True, exist_ok=True)
        local_handler = logging.handlers.RotatingFileHandler(
            local_log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        local_handler.setFormatter(fmt)
        local_handler.setLevel(logging.WARNING)  # solo WARNING+ en local
        root.addHandler(local_handler)

    # 3. Consola (útil en desarrollo; en AWS se puede quitar)
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    console.setLevel(logging.INFO)
    root.addHandler(console)

    logging.getLogger(__name__).info(
        "Remote logging configurado: componente=%r → %s",
        component, mundo_address,
    )
    return remote_handler
