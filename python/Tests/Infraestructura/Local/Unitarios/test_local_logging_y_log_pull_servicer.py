# Tests/Infraestructura/Local/Unitarios/test_local_logging_y_log_pull_servicer.py
"""
test_local_logging_y_log_pull_servicer.py — Cierra el hueco de Log/
que quedaba: local_logging.py (modo local) y log_pull_servicer.py
(lado servidor del RPC PullLogs, modo remoto).
"""

import logging

import pytest

from Infraestructura.Gestores.Log.local_logging import setup_local_logging
from Infraestructura.Gestores.Log.log_pull_servicer import (
    LogPullServicer,
    LogPullServicerAsync,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import (
    log_pull_service_pb2,
    log_service_pb2,
)

# ── local_logging.py ────────────────────────────────────────────────


@pytest.fixture
def root_logger_aislado():
    """
    setup_local_logging() solo añade handlers si el logger raíz está
    completamente limpio (`if not root.handlers`) — se vacía y se
    restaura para poder probar ambos escenarios sin depender de si
    pytest (u otro test anterior) ya le añadió algún handler.
    """
    root = logging.getLogger()
    handlers_previos = list(root.handlers)
    nivel_previo = root.level
    root.handlers = []
    yield root
    root.handlers = handlers_previos
    root.setLevel(nivel_previo)


@pytest.mark.unit
def test_setup_local_logging_crea_fichero_cuando_root_esta_limpio(
    tmp_path, root_logger_aislado
):
    setup_local_logging(component="gestor_bots", log_dir=tmp_path)

    log_path = tmp_path / "Bots" / "Gestor" / "gestor_bots.log"
    assert log_path.exists()
    assert len(root_logger_aislado.handlers) == 2  # fichero + consola


@pytest.mark.unit
def test_setup_local_logging_no_hace_nada_si_root_ya_tenia_handlers(
    tmp_path, root_logger_aislado
):
    """
    HALLAZGO (ya sospechado por los propios autores del proyecto — ver
    comentario en gestor_mundo_server.py sobre este mismo guard): si el
    logger raíz ya tenía CUALQUIER handler configurado de antemano,
    esta función es un no-op silencioso — el fichero de log nunca se
    crea, sin ningún aviso. En un proceso donde algo más (otra
    librería, un test anterior, etc.) ya tocó el logger raíz antes de
    llamar a setup_local_logging(), el componente se queda sin logs a
    fichero sin que nada lo indique.
    """
    root_logger_aislado.addHandler(logging.NullHandler())

    setup_local_logging(component="gestor_bots", log_dir=tmp_path)

    log_path = tmp_path / "Bots" / "Gestor" / "gestor_bots.log"
    assert not log_path.exists()


# ── log_pull_servicer.py ─────────────────────────────────────────────


class FakeHandler:
    """Doble de BufferedLogHandler — solo necesita drain()."""

    def __init__(self, registros):
        self._registros = registros

    def drain(self):
        return self._registros


@pytest.mark.unit
def test_log_pull_servicer_sincrono_devuelve_los_registros_del_handler():
    registros = [log_service_pb2.LogRecord(component="hv_00", message="hola")]
    servicer = LogPullServicer(FakeHandler(registros))

    resp = servicer.PullLogs(log_pull_service_pb2.PullLogsRequest(), context=None)

    assert list(resp.records) == registros


@pytest.mark.unit
async def test_log_pull_servicer_async_devuelve_los_registros_del_handler():
    registros = [log_service_pb2.LogRecord(component="gestor_bots", message="hola")]
    servicer = LogPullServicerAsync(FakeHandler(registros))

    resp = await servicer.PullLogs(log_pull_service_pb2.PullLogsRequest(), context=None)

    assert list(resp.records) == registros
