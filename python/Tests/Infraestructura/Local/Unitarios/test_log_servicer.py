# Tests/Infraestructura/Local/Unitarios/test_log_servicer.py
"""
test_log_servicer.py — Pruebas unitarias de LogServicer: escritura a
disco de LogRecord recogidos por pull, categorizados por componente
(ver log_categorias.py), con caché de logger Python por componente
para no duplicar handlers en escrituras sucesivas.
"""

import logging

import pytest

from Infraestructura.Gestores.Log.log_servicer import LogServicer
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import log_service_pb2


def _log_record(component: str, message: str, level=log_service_pb2.INFO):
    return log_service_pb2.LogRecord(
        component=component,
        level=level,
        logger=component,
        message=message,
        timestamp=1_700_000_000_000,
        exc_info="",
    )


@pytest.fixture
def limpiar_loggers_remote():
    """
    Los loggers Python creados vía logging.getLogger('remote.<comp>')
    son globales por nombre — se limpian sus handlers al terminar cada
    test para que no se acumulen entre tests que reusen el mismo
    nombre de componente.
    """
    creados_antes = set(logging.Logger.manager.loggerDict.keys())
    yield
    for nombre in set(logging.Logger.manager.loggerDict.keys()) - creados_antes:
        if nombre.startswith("remote."):
            logger = logging.getLogger(nombre)
            for h in list(logger.handlers):
                logger.removeHandler(h)
                h.close()


@pytest.mark.unit
def test_escribir_crea_fichero_en_la_subcarpeta_del_componente(
    tmp_path, limpiar_loggers_remote
):
    servicer = LogServicer(log_dir=tmp_path)

    servicer.escribir(_log_record("gestor_bots", "hola desde gestor_bots"))

    log_path = tmp_path / "Bots" / "Gestor" / "gestor_bots.log"
    assert log_path.exists()
    assert "hola desde gestor_bots" in log_path.read_text()


@pytest.mark.unit
def test_escribir_componente_desconocido_usa_raiz_de_log_dir(
    tmp_path, limpiar_loggers_remote
):
    servicer = LogServicer(log_dir=tmp_path)

    servicer.escribir(_log_record("componente_rarisimo", "mensaje"))

    log_path = tmp_path / "componente_rarisimo.log"
    assert log_path.exists()


@pytest.mark.unit
def test_escribir_repetido_no_duplica_handlers(tmp_path, limpiar_loggers_remote):
    servicer = LogServicer(log_dir=tmp_path)

    servicer.escribir(_log_record("gestor_bots", "primero"))
    servicer.escribir(_log_record("gestor_bots", "segundo"))

    logger_componente = servicer._loggers["gestor_bots"]
    assert len(logger_componente.handlers) == 1
