# Tests/Infraestructura/Remoto/Integracion/test_crear_elemento_accion.py


"""
Prueba Acciones/crear_elemento.py aislando:
  - el cuestionario real (se monkeypatchea ejecutar_cuestionario para
    no depender de input() de verdad -- eso ya lo cubre
    test_cuestionario.py, si existe, no hace falta repetirlo aquí).
  - ComunicacionesLocal real (se usa un doble simple).

Usa una clase de elemento DE PRUEBA, registrada temporalmente en
ELEMENTOS vía monkeypatch, para no depender de que Piedra y sus
comportamientos estén terminados -- así este test no se rompe ni se
bloquea por el estado de otras piezas en desarrollo.
"""

import json

import pytest

from Infraestructura.Gestores.Consola.Acciones import crear_elemento as accion_modulo
from Infraestructura.Gestores.Consola import catalogo_campos as catalogo_modulo
from Infraestructura.Gestores.Consola.cuestionario import CampoCuestionario


class _ElementoDePrueba:
    """Doble mínimo de un Elemento real -- solo lo que usa el handler."""

    @classmethod
    def campos_para_creacion(cls):
        return ["casilla", "peso"]


class _FakeComunicaciones:
    def __init__(self, respuesta=(True, "", 42)):
        self._respuesta = respuesta
        self.llamada: dict = {}

    async def construir_elemento(self, pos, nombre_clase, campos: bytes):
        self.llamada = {"pos": pos, "nombre_clase": nombre_clase, "campos": campos}
        return self._respuesta


@pytest.fixture
def elementos_de_prueba(monkeypatch):
    monkeypatch.setitem(accion_modulo.ELEMENTOS, "ElementoDePrueba", _ElementoDePrueba)
    return "ElementoDePrueba"


async def test_crear_elemento_exito(monkeypatch, elementos_de_prueba):
    valores_simulados = {"casilla": (3, 4), "peso": 2.5}
    monkeypatch.setattr(
        accion_modulo, "ejecutar_cuestionario", _async_devuelve(valores_simulados)
    )

    comunicaciones = _FakeComunicaciones(respuesta=(True, "", 42))
    resultado = await accion_modulo._handler(comunicaciones, elementos_de_prueba)

    assert "42" in resultado
    assert comunicaciones.llamada["pos"] == (3, 4)
    assert comunicaciones.llamada["nombre_clase"] == elementos_de_prueba
    campos_enviados = json.loads(comunicaciones.llamada["campos"].decode())
    assert campos_enviados == {"casilla": [3, 4], "peso": 2.5}  # JSON no tiene tuplas


async def test_crear_elemento_falla_si_falta_casilla(monkeypatch, elementos_de_prueba):
    """Si campos_para_creacion() no incluye 'casilla', no se sabe dónde
    colocar el elemento -- debe fallar explícito, no adivinar una posición."""
    monkeypatch.setattr(
        _ElementoDePrueba, "campos_para_creacion", classmethod(lambda cls: ["peso"])
    )
    monkeypatch.setattr(
        accion_modulo, "ejecutar_cuestionario", _async_devuelve({"peso": 1.0})
    )

    comunicaciones = _FakeComunicaciones()
    resultado = await accion_modulo._handler(comunicaciones, elementos_de_prueba)

    assert "casilla" in resultado.lower()
    assert "error" in resultado.lower()
    assert comunicaciones.llamada == {}  # no debe haber llegado a llamar a la red


async def test_crear_elemento_falla_si_campo_no_esta_en_catalogo(
    monkeypatch, elementos_de_prueba
):
    monkeypatch.setattr(
        _ElementoDePrueba,
        "campos_para_creacion",
        classmethod(lambda cls: ["casilla", "campo_inventado"]),
    )

    comunicaciones = _FakeComunicaciones()
    resultado = await accion_modulo._handler(comunicaciones, elementos_de_prueba)

    assert "campo_inventado" in resultado
    assert "catalogo_campos" in resultado
    assert comunicaciones.llamada == {}


async def test_crear_elemento_propaga_error_del_servidor(
    monkeypatch, elementos_de_prueba
):
    monkeypatch.setattr(
        accion_modulo,
        "ejecutar_cuestionario",
        _async_devuelve({"casilla": (0, 0), "peso": 1.0}),
    )
    comunicaciones = _FakeComunicaciones(
        respuesta=(False, "peso no puede ser negativo", 0)
    )

    resultado = await accion_modulo._handler(comunicaciones, elementos_de_prueba)

    assert "peso no puede ser negativo" in resultado


def test_parse_nombre_clase_valido():
    from Infraestructura.Gestores.Consola.cuestionario import parse_nombre_clase

    assert parse_nombre_clase("Piedra") == "Piedra"


def test_parse_nombre_clase_invalido():
    from Infraestructura.Gestores.Consola.cuestionario import parse_nombre_clase

    with pytest.raises(ValueError):
        parse_nombre_clase("EstoNoExiste")


def _async_devuelve(valor):
    async def _fake(*args, **kwargs):
        return valor

    return _fake
