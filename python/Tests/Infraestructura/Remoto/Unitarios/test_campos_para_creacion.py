# Tests/Infraestructura/Remoto/test_campos_para_creacion.py
"""
Cubre el contrato de campos_para_creacion() / ayuda_creacion():
- la clase base (Comportamiento/Elemento) debe fallar alto si no se
  sobrescribe.
- Peso, ya implementado, debe devolver exactamente lo esperado.
- Piedra debe agregar en una lista PLANA de strings -- este es el caso
  que reprodujo el bug real (TypeError: unhashable type: 'list',
  causado por olvidar el '*' al combinar el resultado de un
  comportamiento).
"""

import pytest

from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Elementos.Simples.Piedra.piedra import Piedra
from Core.Entities.Elementos.Simples.Piedra import piedra as piedra_module


def test_comportamiento_base_campos_para_creacion_falla_alto():
    class ComportamientoSinImplementar(Comportamiento):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    with pytest.raises(NotImplementedError):
        ComportamientoSinImplementar.campos_para_creacion()


def test_comportamiento_base_ayuda_creacion_falla_alto():
    class ComportamientoSinImplementar(Comportamiento):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    with pytest.raises(NotImplementedError):
        ComportamientoSinImplementar.ayuda_creacion()


def test_peso_campos_para_creacion():
    assert Peso.campos_para_creacion() == ["peso"]


def test_peso_ayuda_creacion_no_vacio():
    texto = Peso.ayuda_creacion()
    assert isinstance(texto, str)
    assert texto.strip() != ""


def _parchear_comportamientos_pendientes(monkeypatch):
    """
    Empujable/Volumen/Color/Termico puede que aún no implementen
    campos_para_creacion() -- se les da una implementación mínima de
    prueba SOLO para poder ejercitar la agregación de Piedra sin
    esperar a que estén terminados de verdad. Si para cuando leas esto
    ya están implementados, monkeypatch los sobrescribe igual sin
    romper nada (se deshace solo al acabar el test).
    """
    for nombre_atributo in ("Empujable", "Volumen", "Color", "Termico"):
        clase = getattr(piedra_module, nombre_atributo, None)
        if clase is None:
            pytest.skip(
                f"piedra.py no importa '{nombre_atributo}' -- ajusta el "
                "nombre en este test si se ha renombrado el import."
            )
        monkeypatch.setattr(
            clase,
            "campos_para_creacion",
            classmethod(lambda cls: [f"campo_{cls.__name__.lower()}"]),
        )


def test_piedra_campos_para_creacion_es_lista_plana_de_strings(monkeypatch):
    _parchear_comportamientos_pendientes(monkeypatch)

    campos = Piedra.campos_para_creacion()

    assert isinstance(campos, list)
    for campo in campos:
        assert isinstance(campo, str), (
            f"campos_para_creacion() debe devolver strings sueltos, "
            f"encontrado {campo!r} ({type(campo).__name__}) -- probable "
            f"'*' olvidado al combinar el resultado de un comportamiento."
        )


def test_piedra_campos_para_creacion_incluye_campos_propios_y_de_peso(monkeypatch):
    _parchear_comportamientos_pendientes(monkeypatch)

    campos = Piedra.campos_para_creacion()

    for esperado in ("tamanho", "casilla", "capa", "peso"):
        assert (
            esperado in campos
        ), f"falta '{esperado}' en campos_para_creacion() de Piedra"


def test_piedra_ayuda_creacion_no_vacio():
    texto = Piedra.ayuda_creacion()
    assert isinstance(texto, str)
    assert texto.strip() != ""


def test_comportamiento_de_campo_encuentra_peso():
    assert Piedra._comportamiento_de_campo("peso") is Peso


def test_comportamiento_de_campo_campo_propio_devuelve_none():
    # 'casilla' es de Elemento_Simple, no de ningún Comportamiento --
    # ver el hueco señalado explícitamente en el diseño de consola.py.
    assert Piedra._comportamiento_de_campo("casilla") is None


def test_comportamiento_de_campo_campo_inexistente_devuelve_none():
    assert Piedra._comportamiento_de_campo("no_existe_este_campo") is None
