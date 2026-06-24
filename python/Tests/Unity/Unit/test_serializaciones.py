# Test/Conexion_Visualizador/Unit/test_serializaciones.py

from unittest.mock import patch

import pytest

from Services.Serializaciones.actualizacion import serializacion_actualizacion
from Services.Serializaciones.bots import serializacion_completa_bot, serializar_bots
from Services.Serializaciones.mundo import serializar_mundo

# ── serializar_bots ───────────────────────────────────────────────────────────


def test_serializar_bots_devuelve_lista(shared_data, bot_position_dict):
    resultado = serializar_bots(shared_data["bots"])
    assert isinstance(resultado, list)
    assert len(resultado) == 1
    assert resultado[0] == bot_position_dict


def test_serializar_bots_vacio():
    assert serializar_bots({}) == []


def test_serializar_bots_multiples(bot_position_dict, bot_full_dict):
    bot_a = type("Bot", (), {"serialize_position": lambda self: {"id": "a"}})()
    bot_b = type("Bot", (), {"serialize_position": lambda self: {"id": "b"}})()
    resultado = serializar_bots({"a": bot_a, "b": bot_b})
    assert len(resultado) == 2
    ids = [b["id"] for b in resultado]
    assert "a" in ids and "b" in ids


# ── serializacion_completa_bot ────────────────────────────────────────────────


def test_serializacion_completa_bot(mock_bot, bot_full_dict):
    assert serializacion_completa_bot(mock_bot) == bot_full_dict


# ── serializar_mundo ──────────────────────────────────────────────────────────


def test_serializar_mundo_stub_devuelve_dict():
    assert isinstance(serializar_mundo(None), dict)


# ── serializacion_actualizacion ───────────────────────────────────────────────


def test_serializacion_actualizacion_estructura(shared_data, bot_position_dict):
    resultado = serializacion_actualizacion(shared_data)

    assert resultado["tipo"] == "actualizacion"
    assert isinstance(resultado["bots"], list)
    assert isinstance(resultado["mundo"], dict)
    assert resultado["bots"][0] == bot_position_dict


def test_serializacion_actualizacion_sin_bots(shared_data):
    shared_data["bots"] = {}
    resultado = serializacion_actualizacion(shared_data)
    assert resultado["bots"] == []
