# Tests/Infraestructura/Remoto/Unitarios/test_api_acciones.py
"""
test_api_acciones.py — Pruebas unitarias de las funciones de consulta
de api_acciones.py (Gestores/Mundo/Logica_Mundo/api_acciones.py):
get_coste, accion_conocida, listar. Pequeño y sin dependencias, pero
sin ningún test hasta ahora.
"""

import pytest

from Infraestructura.Gestores.Mundo.Logica_Mundo.api_acciones import (
    accion_conocida,
    get_coste,
    listar,
)


@pytest.mark.unit
def test_get_coste_de_accion_conocida():
    assert get_coste("mirar") == 1


@pytest.mark.unit
def test_get_coste_de_accion_desconocida_es_cero():
    assert get_coste("accion_que_no_existe") == 0


@pytest.mark.unit
def test_accion_conocida_true_para_registrada():
    assert accion_conocida("mirar") is True


@pytest.mark.unit
def test_accion_conocida_false_para_no_registrada():
    assert accion_conocida("accion_que_no_existe") is False


@pytest.mark.unit
def test_listar_incluye_las_acciones_registradas():
    nombres = listar()
    assert "mirar" in nombres
