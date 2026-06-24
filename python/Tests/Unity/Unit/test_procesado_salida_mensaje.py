# Test/Conexion_Visualizador/Unit/test_procesado_salida_mensaje.py

import json
from unittest.mock import patch, MagicMock

import pytest

from Services.Conexion_Visualizador.procesado_salida_mensaje import procesar_mensaje_salida

_BASE = "Services.Conexion_Visualizador.procesado_salida_mensaje"


# ── actualizacion ─────────────────────────────────────────────────────────────

def test_actualizacion_devuelve_bytes_json(shared_data):
    respuesta_dict = {"tipo": "actualizacion", "bots": [], "mundo": {}}

    with patch(f"{_BASE}.salida_actualizacion", return_value=respuesta_dict):
        resultado = procesar_mensaje_salida({"peticion": "actualizacion"}, shared_data)

    assert isinstance(resultado, bytes)
    assert json.loads(resultado) == respuesta_dict


# ── dato ──────────────────────────────────────────────────────────────────────

def test_dato_devuelve_bytes_json(shared_data):
    respuesta_dict = {"tipo": "dato", "bot": {"id": "bot_1"}}

    with patch(f"{_BASE}.salida_dato", return_value=respuesta_dict):
        resultado = procesar_mensaje_salida(
            {"peticion": "dato", "entity": "bot", "id": "bot_1"}, shared_data
        )

    assert isinstance(resultado, bytes)
    assert json.loads(resultado) == respuesta_dict


# ── mapa ──────────────────────────────────────────────────────────────────────

def test_mapa_devuelve_none_cuando_stub(shared_data):
    with patch(f"{_BASE}.salida_mapa", return_value=None):
        resultado = procesar_mensaje_salida({"peticion": "mapa"}, shared_data)

    assert resultado is None


# ── perfil ────────────────────────────────────────────────────────────────────

def test_perfil_devuelve_bytes_json(shared_data):
    respuesta_dict = {"peticion": "perfil", "tipo": "obtener_perfiles", "perfiles": []}

    with patch(f"{_BASE}.salida_perfil", return_value=respuesta_dict):
        resultado = procesar_mensaje_salida(
            {"peticion": "perfil", "tipo": "obtener_perfiles"}, shared_data
        )

    assert isinstance(resultado, bytes)
    assert json.loads(resultado) == respuesta_dict


# ── pausa ─────────────────────────────────────────────────────────────────────

def test_pausa_es_fire_and_forget(shared_data):
    with patch(f"{_BASE}.salida_pause") as mock_pause:
        resultado = procesar_mensaje_salida({"peticion": "pausa"}, shared_data)

    mock_pause.assert_called_once_with(shared_data)
    assert resultado is None


# ── petición desconocida ──────────────────────────────────────────────────────

def test_peticion_desconocida_devuelve_none(shared_data):
    resultado = procesar_mensaje_salida({"peticion": "no_existe"}, shared_data)
    assert resultado is None


def test_peticion_ausente_devuelve_none(shared_data):
    resultado = procesar_mensaje_salida({}, shared_data)
    assert resultado is None


# ── handler devuelve None ─────────────────────────────────────────────────────

def test_handler_devuelve_none_no_envia_nada(shared_data):
    with patch(f"{_BASE}.salida_actualizacion", return_value=None):
        resultado = procesar_mensaje_salida({"peticion": "actualizacion"}, shared_data)

    assert resultado is None
