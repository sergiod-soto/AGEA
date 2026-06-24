# Test/Conexion_Visualizador/Unit/test_salida_datos.py

from unittest.mock import patch

import pytest

from Services.Conexion_Visualizador.Salida_Datos.Entidades.salida_bot import (
    salida_bot_full,
)
from Services.Conexion_Visualizador.Salida_Datos.salida_dato import salida_dato
from Services.Conexion_Visualizador.Salida_Datos.salida_error import salida_error
from Services.Conexion_Visualizador.Salida_Datos.salida_pause import salida_pause
from Services.Conexion_Visualizador.Salida_Datos.salida_perfil import (
    salida_perfil,
    _obtener_perfil,
)

# ── salida_bot_full ───────────────────────────────────────────────────────────


def test_salida_bot_full_devuelve_dict(shared_data, bot_full_dict):
    resultado = salida_bot_full(shared_data, {"id": "bot_1"})
    assert resultado == bot_full_dict


def test_salida_bot_full_id_inexistente_devuelve_none(shared_data):
    resultado = salida_bot_full(shared_data, {"id": "no_existe"})
    assert resultado is None


# ── salida_dato ───────────────────────────────────────────────────────────────


def test_salida_dato_bot_devuelve_dict_con_tipo(shared_data, bot_full_dict):
    resultado = salida_dato(shared_data, {"entity": "bot", "id": "bot_1"})
    assert resultado == {"tipo": "dato", "bot": bot_full_dict}


def test_salida_dato_entidad_desconocida_devuelve_none(shared_data):
    resultado = salida_dato(shared_data, {"entity": "terreno", "id": "x"})
    assert resultado is None


def test_salida_dato_entity_ausente_devuelve_none(shared_data):
    resultado = salida_dato(shared_data, {})
    assert resultado is None


def test_salida_dato_bot_inexistente_devuelve_none(shared_data):
    resultado = salida_dato(shared_data, {"entity": "bot", "id": "no_existe"})
    assert resultado is None


# ── salida_error ──────────────────────────────────────────────────────────────


def test_salida_error_devuelve_dict_con_campos():
    resultado = salida_error(404, "fichero no encontrado")
    assert resultado == {
        "tipo": "error",
        "codigo": "404",
        "datos": "fichero no encontrado",
    }


def test_salida_error_codigo_como_string():
    resultado = salida_error("ERR_01", "algo falló")
    assert resultado["codigo"] == "ERR_01"


# ── salida_pause ──────────────────────────────────────────────────────────────


def test_salida_pause_alterna_pausa(shared_data):
    assert shared_data["other"]["paused"] is False
    salida_pause(shared_data)
    assert shared_data["other"]["paused"] is True
    salida_pause(shared_data)
    assert shared_data["other"]["paused"] is False


def test_salida_pause_devuelve_none(shared_data):
    assert salida_pause(shared_data) is None


# ── salida_perfil ─────────────────────────────────────────────────────────────

_PERFIL_MOCK = {
    "id": "perfil1",
    "nombre": "sergiod",
    "fecha": "01-01-2026",
    "tiempo_entrenamiento": 14,
}


def test_obtener_perfil_devuelve_dict(shared_data):
    with patch(
        "Services.Conexion_Visualizador.Salida_Datos.salida_perfil.leer_JSON_Datos",
        return_value=_PERFIL_MOCK,
    ):
        resultado = _obtener_perfil(1)

    assert resultado == _PERFIL_MOCK


def test_obtener_perfil_error_lectura_devuelve_none():
    with patch(
        "Services.Conexion_Visualizador.Salida_Datos.salida_perfil.leer_JSON_Datos",
        side_effect=FileNotFoundError,
    ):
        resultado = _obtener_perfil(1)

    assert resultado is None


def test_salida_perfil_obtener_perfiles_devuelve_6(shared_data):
    with patch(
        "Services.Conexion_Visualizador.Salida_Datos.salida_perfil.leer_JSON_Datos",
        return_value=_PERFIL_MOCK,
    ):
        resultado = salida_perfil(shared_data, {"tipo": "obtener_perfiles"})

    assert resultado["tipo"] == "obtener_perfiles"
    assert resultado["peticion"] == "perfil"
    assert len(resultado["perfiles"]) == 6


def test_salida_perfil_tipo_desconocido_devuelve_none(shared_data):
    resultado = salida_perfil(shared_data, {"tipo": "no_existe"})
    assert resultado is None


def test_salida_perfil_perfiles_con_error_se_omiten(shared_data):
    """Si un perfil falla al leerse, se omite sin romper el resto."""
    call_count = 0

    def leer_con_fallo(num):
        nonlocal call_count
        call_count += 1
        if num == 3:
            raise FileNotFoundError
        return _PERFIL_MOCK

    with patch(
        "Services.Conexion_Visualizador.Salida_Datos.salida_perfil.leer_JSON_Datos",
        side_effect=leer_con_fallo,
    ):
        resultado = salida_perfil(shared_data, {"tipo": "obtener_perfiles"})

    assert len(resultado["perfiles"]) == 5
