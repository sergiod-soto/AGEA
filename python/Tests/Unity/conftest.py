# Test/Conexion_Visualizador/conftest.py

import pytest


# ── shared_data ───────────────────────────────────────────────────────────────

@pytest.fixture
def bot_position_dict():
    return {
        "id": "bot_1",
        "tamanho": 1,
        "distancia_visible": 5,
        "casilla": {"x": 3, "y": 4},
        "rotacion": 90,
    }


@pytest.fixture
def bot_full_dict(bot_position_dict):
    return {
        **bot_position_dict,
        "apellidos": ["alpha", "beta"],
        "adn": [1, 2, 3],
        "stats": {"salud": 100, "energia": 80},
        "padres": ["padre_1", "madre_1"],
    }


@pytest.fixture
def mock_bot(bot_position_dict, bot_full_dict):
    """Bot con serialize_position y serialize_all devolviendo dicts."""
    bot = type("Bot", (), {
        "serialize_position": lambda self: bot_position_dict,
        "serialize_all":      lambda self: bot_full_dict,
    })()
    return bot


@pytest.fixture
def shared_data(mock_bot):
    return {
        "bots":  {"bot_1": mock_bot},
        "mundo": None,
        "other": {"paused": False, "1/fps/1000": 500, "conn_ready": False},
        "dev":   {},
    }
