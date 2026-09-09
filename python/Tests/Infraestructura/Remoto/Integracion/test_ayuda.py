# Tests/Infraestructura/Remoto/Integracion/test_ayuda.py


"""
Cubre _mostrar_ayuda() y su búsqueda en los tres catálogos: ACCIONES,
ELEMENTOS, COMPORTAMIENTOS. El caso 'ayuda piedra' es exactamente el
que reprodujo el TypeError original -- se deja como test explícito
para que no vuelva a colarse.
"""

import pytest

from Infraestructura.Gestores.Consola import consola
from Infraestructura.Gestores.Consola.registry import ACCIONES


def test_buscar_por_nombre_case_insensitive():
    resultado = consola._buscar_por_nombre({"Piedra": object()}, "piedra")
    assert resultado is not None


def test_buscar_por_nombre_no_encontrado():
    assert consola._buscar_por_nombre({"Piedra": object()}, "no_existe") is None


def test_mostrar_ayuda_sin_argumento_lista_comandos(capsys):
    consola._mostrar_ayuda(None)
    salida = capsys.readouterr().out
    assert "Comandos disponibles" in salida
    for nombre in ACCIONES:
        assert nombre in salida


def test_mostrar_ayuda_comando_conocido(capsys):
    consola._mostrar_ayuda("tick_rate")
    salida = capsys.readouterr().out
    assert "tick_rate" in salida
    assert "ticks_per_second" in salida


def test_mostrar_ayuda_piedra_no_revienta(capsys):
    """
    Regresión directa del bug reportado: 'ayuda piedra' no debe lanzar
    TypeError (ni ninguna otra excepción) aunque algunos comportamientos
    de Piedra todavía no implementen campos_para_creacion().
    """
    consola._mostrar_ayuda("piedra")
    salida = capsys.readouterr().out
    assert "Piedra" in salida


def test_mostrar_ayuda_piedra_muestra_peso_con_comportamiento(capsys, monkeypatch):
    from Core.Entities.Elementos.Simples.Piedra import piedra as piedra_module

    for nombre_atributo in ("Empujable", "Volumen", "Color", "Termico"):
        clase = getattr(piedra_module, nombre_atributo, None)
        if clase is None:
            pytest.skip(f"'{nombre_atributo}' no está en piedra.py")
        monkeypatch.setattr(clase, "campos_para_creacion", classmethod(lambda cls: []))
        monkeypatch.setattr(
            clase, "ayuda_creacion", classmethod(lambda cls: f"ayuda de {cls.__name__}")
        )

    consola._mostrar_ayuda("piedra")
    salida = capsys.readouterr().out
    assert "peso (Peso)" in salida or "peso" in salida
    assert "masa" in salida.lower()  # texto real de Peso.ayuda_creacion()


def test_mostrar_ayuda_peso_como_comportamiento(capsys):
    consola._mostrar_ayuda("peso")
    salida = capsys.readouterr().out
    assert "masa" in salida.lower()


def test_mostrar_ayuda_elemento_sin_implementar_no_revienta(capsys):
    """
    Un elemento real que aún no implementa campos_para_creacion()
    (ej. Agua, a día de escribir esto) debe mostrar el mensaje de
    NotImplementedError de forma controlada, no propagar la excepción.
    """
    consola._mostrar_ayuda("agua")
    salida = capsys.readouterr().out
    assert "Agua" in salida or "no implementa" in salida.lower()


def test_mostrar_ayuda_argumento_desconocido(capsys):
    consola._mostrar_ayuda("esto_no_existe_seguro")
    salida = capsys.readouterr().out
    assert "no es un comando" in salida.lower()
