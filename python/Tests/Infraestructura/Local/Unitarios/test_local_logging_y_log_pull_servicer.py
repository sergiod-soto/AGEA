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
from Infraestructura.Gestores.Log import (
    local_logging,
)  # para espiar local_logging.logger

# ── local_logging.py ────────────────────────────────────────────────


@pytest.fixture
def root_logger_aislado():
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
    root_logger_aislado.handlers = (
        []
    )  # limpia también los handlers que pytest añadió en fase "call"

    setup_local_logging(component="gestor_bots", log_dir=tmp_path)

    log_path = tmp_path / "Bots" / "Gestor" / "gestor_bots.log"
    assert log_path.exists()
    assert len(root_logger_aislado.handlers) == 2  # fichero + consola


@pytest.mark.unit
def test_setup_local_logging_no_hace_nada_si_root_ya_tenia_handlers(
    tmp_path, root_logger_aislado, monkeypatch
):
    avisos = []
    monkeypatch.setattr(
        local_logging.logger,
        "warning",
        lambda msg, *args, **kwargs: avisos.append(msg % args if args else msg),
    )

    root_logger_aislado.handlers = []  # idem: limpia lo que pytest metió en fase "call"
    root_logger_aislado.addHandler(
        logging.NullHandler()
    )  # y ahora sí, el handler que queremos simular

    setup_local_logging(component="gestor_bots", log_dir=tmp_path)

    log_path = tmp_path / "Bots" / "Gestor" / "gestor_bots.log"
    assert not log_path.exists()
    assert len(avisos) == 1
    assert "gestor_bots" in avisos[0]

    assert len(avisos) == 1
    assert "gestor_bots" in avisos[0]


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


@pytest.mark.unit
def test_setup_local_logging_no_hace_nada_si_root_ya_tenia_handlers(
    tmp_path, root_logger_aislado, caplog
):
    """
    Si el logger raíz ya tenía CUALQUIER handler configurado de antemano,
    setup_local_logging() no crea el fichero de log (no toca el
    filesystem) y en su lugar emite un logger.warning explícito, para
    que el hecho de que el componente se quede sin logs a fichero no
    pase desapercibido.
    """
    root_logger_aislado.addHandler(logging.NullHandler())

    with caplog.at_level(
        logging.WARNING, logger="Infraestructura.Gestores.Log.local_logging"
    ):
        setup_local_logging(component="gestor_bots", log_dir=tmp_path)

    log_path = tmp_path / "Bots" / "Gestor" / "gestor_bots.log"
    assert not log_path.exists()

    assert any(
        record.levelno == logging.WARNING and "gestor_bots" in record.message
        for record in caplog.records
    )
