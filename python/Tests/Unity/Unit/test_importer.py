# Test/Conexion_Visualizador/Unit/test_importer.py

import json
from unittest.mock import patch

import pytest

from Services.Conexion_Visualizador.importer import receive_data


# ── helpers ───────────────────────────────────────────────────────────────────

def _encode(d: dict) -> bytes:
    return json.dumps(d).encode()


# ── JSON válido ───────────────────────────────────────────────────────────────

def test_receive_data_llama_procesar_y_devuelve_respuesta(shared_data):
    mensaje = {"peticion": "actualizacion"}
    respuesta_mock = b"respuesta"

    with patch(
        "Services.Conexion_Visualizador.importer.procesar_mensaje_salida",
        return_value=respuesta_mock,
    ) as mock_procesar:
        resultado = receive_data(_encode(mensaje), shared_data)

    mock_procesar.assert_called_once_with(mensaje, shared_data)
    assert resultado == respuesta_mock


def test_receive_data_devuelve_none_si_procesar_devuelve_none(shared_data):
    mensaje = {"peticion": "pausa"}

    with patch(
        "Services.Conexion_Visualizador.importer.procesar_mensaje_salida",
        return_value=None,
    ):
        resultado = receive_data(_encode(mensaje), shared_data)

    assert resultado is None


# ── JSON inválido ─────────────────────────────────────────────────────────────

def test_receive_data_json_invalido_devuelve_none(shared_data):
    resultado = receive_data(b"esto no es json{{{", shared_data)
    assert resultado is None


def test_receive_data_bytes_vacios_devuelve_none(shared_data):
    resultado = receive_data(b"", shared_data)
    assert resultado is None


def test_receive_data_solo_espacios_devuelve_none(shared_data):
    resultado = receive_data(b"   ", shared_data)
    assert resultado is None
