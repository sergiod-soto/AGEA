# Tests/Infraestructura/Remoto/Integracion/test_consola_loop.py


"""
Prueba iniciar() simulando stdin, sin gRPC real (comunicaciones=None
basta: ninguna de las líneas usadas aquí llega a tocarlo).
"""

import pytest

from Infraestructura.Gestores.Consola.consola import iniciar


def _simular_input(monkeypatch, lineas: list[str]):
    """
    Sustituye asyncio.to_thread(input, prompt) por un generador que
    devuelve las líneas dadas en orden, y EOFError si se piden más de
    las que hay -- así el bucle de consola termina solo si algo se
    queda esperando indefinidamente.
    """
    iterador = iter(lineas)

    async def _fake_to_thread(func, *args, **kwargs):
        try:
            return next(iterador)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("asyncio.to_thread", _fake_to_thread)


async def test_ayuda_piedra_luego_salir_no_revienta(monkeypatch, capsys):
    _simular_input(monkeypatch, ["ayuda piedra", "salir"])

    await iniciar(comunicaciones=None)

    salida = capsys.readouterr().out
    assert "Traceback" not in salida
    assert "Piedra" in salida
    assert "Cerrando consola" in salida


async def test_comando_desconocido_no_revienta(monkeypatch, capsys):
    _simular_input(monkeypatch, ["esto_no_existe", "salir"])

    await iniciar(comunicaciones=None)

    salida = capsys.readouterr().out
    assert "Comando desconocido" in salida


async def test_eof_termina_limpio(monkeypatch, capsys):
    _simular_input(monkeypatch, [])  # primer input() ya lanza EOFError

    await iniciar(comunicaciones=None)  # no debe colgarse ni reventar

    salida = capsys.readouterr().out
    assert "Traceback" not in salida
