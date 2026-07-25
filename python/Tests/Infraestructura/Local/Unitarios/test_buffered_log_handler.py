# Tests/Infraestructura/Local/Unitarios/test_buffered_log_handler.py
"""
test_buffered_log_handler.py — Pruebas unitarias de BufferedLogHandler:
acumulación en memoria (modelo pull, sin red), vaciado con drain(), y
la política de descarte cuando el buffer se llena sin que nadie haga
pull todavía (prioriza no perder WARNING+ frente a DEBUG/INFO).
"""

import logging

import pytest

from Infraestructura.Gestores.Log.buffered_log_handler import (
    BufferedLogHandler,
    setup_buffered_logging,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Otros import log_service_pb2


def _record(level: int, message: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="test",
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )


@pytest.mark.unit
def test_emit_agrega_registro_al_buffer():
    handler = BufferedLogHandler(component="comp_x")
    handler.emit(_record(logging.INFO, "hola"))

    registros = handler.drain()

    assert len(registros) == 1
    assert registros[0].component == "comp_x"
    assert registros[0].message == "hola"
    assert registros[0].level == log_service_pb2.INFO


@pytest.mark.unit
def test_drain_vacia_el_buffer():
    handler = BufferedLogHandler(component="comp_x")
    handler.emit(_record(logging.INFO, "hola"))

    handler.drain()
    segundo_drain = handler.drain()

    assert segundo_drain == []


@pytest.mark.unit
def test_buffer_lleno_descarta_debug_antes_que_warning():
    """
    Con el buffer lleno de DEBUG/INFO + 1 WARNING, un registro nuevo
    debe desalojar un DEBUG/INFO, nunca el WARNING — ver el bucle de
    emit() que busca `r.level < WARNING` antes de caer al FIFO simple.
    """
    handler = BufferedLogHandler(component="comp_x", buffer_max=3)
    handler.emit(_record(logging.DEBUG, "debug_1"))
    handler.emit(_record(logging.DEBUG, "debug_2"))
    handler.emit(_record(logging.WARNING, "warning_1"))

    handler.emit(_record(logging.INFO, "info_nuevo"))  # 4º registro, buffer ya lleno

    registros = handler.drain()
    mensajes = [r.message for r in registros]

    assert len(registros) == 3
    assert "warning_1" in mensajes  # el WARNING nunca se descarta


@pytest.mark.unit
def test_buffer_lleno_sin_debug_descarta_el_mas_antiguo():
    """Si todos los registros del buffer son WARNING+, se aplica FIFO
    simple: se descarta el más antiguo."""
    handler = BufferedLogHandler(component="comp_x", buffer_max=2)
    handler.emit(_record(logging.WARNING, "warning_1"))
    handler.emit(_record(logging.WARNING, "warning_2"))

    handler.emit(_record(logging.WARNING, "warning_3"))  # fuerza descarte del más viejo

    registros = handler.drain()
    mensajes = [r.message for r in registros]

    assert mensajes == ["warning_2", "warning_3"]


@pytest.fixture
def limpiar_root_logger():
    """
    setup_buffered_logging() añade handlers al logger raíz global — se
    restauran los handlers previos al terminar el test para no
    contaminar el resto de la suite.
    """
    root = logging.getLogger()
    handlers_previos = list(root.handlers)
    nivel_previo = root.level
    yield
    root.handlers = handlers_previos
    root.setLevel(nivel_previo)


@pytest.mark.unit
def test_setup_buffered_logging_conecta_el_handler_al_root(limpiar_root_logger):
    handler = setup_buffered_logging(component="comp_setup", level=logging.DEBUG)

    logging.getLogger("cualquier.modulo").warning("mensaje de prueba")

    registros = handler.drain()
    mensajes = [r.message for r in registros]
    assert "mensaje de prueba" in mensajes
