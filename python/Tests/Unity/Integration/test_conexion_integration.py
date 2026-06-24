# Test/Conexion_Visualizador/Integration/test_conexion_integration.py
#
# Levanta run_exporter en un thread (no proceso) para poder compartir
# shared_data directamente sin Manager. Usa un puerto libre asignado por el OS.

import json
import socket
import threading
import time
from unittest.mock import patch

import pytest

from Services.Conexion_Visualizador import protocolo
from Services.Conexion_Visualizador.conexion import run_exporter


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def servidor(shared_data):
    """
    Arranca run_exporter en un thread y devuelve el puerto en el que escucha.
    Parchamos settings para usar un puerto libre (0 = el OS elige).
    """
    # Encontramos un puerto libre antes de arrancar
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]

    with patch("Services.Conexion_Visualizador.conexion.settings") as mock_settings:
        mock_settings.UNITY_HOST = "127.0.0.1"
        mock_settings.UNITY_PORT = puerto

        t = threading.Thread(
            target=run_exporter,
            args=(shared_data,),
            daemon=True,
        )
        t.start()
        time.sleep(0.05)  # espera mínima a que el socket esté en listen
        yield puerto


@pytest.fixture
def cliente(servidor):
    """Cliente TCP conectado al servidor de test."""
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(("127.0.0.1", servidor))
    yield conn
    conn.close()


# ── helpers ───────────────────────────────────────────────────────────────────

def _enviar_peticion(conn: socket.socket, peticion: dict) -> dict:
    protocolo.enviar(conn, json.dumps(peticion).encode())
    respuesta = protocolo.recibir(conn)
    assert respuesta is not None
    return json.loads(respuesta)


# ── tests ─────────────────────────────────────────────────────────────────────

def test_peticion_actualizacion(cliente, shared_data, bot_position_dict):
    respuesta = _enviar_peticion(cliente, {"peticion": "actualizacion"})

    assert respuesta["tipo"] == "actualizacion"
    assert isinstance(respuesta["bots"], list)
    assert respuesta["bots"][0] == bot_position_dict


def test_peticion_dato_bot(cliente, shared_data, bot_full_dict):
    respuesta = _enviar_peticion(
        cliente, {"peticion": "dato", "entity": "bot", "id": "bot_1"}
    )

    assert respuesta["tipo"] == "dato"
    assert respuesta["bot"] == bot_full_dict


def test_peticion_dato_bot_inexistente_no_responde(cliente, shared_data):
    """Bot inexistente → handler devuelve None → servidor no envía nada."""
    protocolo.enviar(
        cliente,
        json.dumps({"peticion": "dato", "entity": "bot", "id": "no_existe"}).encode(),
    )
    # No hay respuesta: intentamos recibir con timeout corto
    cliente.settimeout(0.3)
    with pytest.raises((socket.timeout, TimeoutError)):
        protocolo.recibir(cliente)


def test_peticion_pausa_no_envia_respuesta(cliente, shared_data):
    """pausa es fire-and-forget: no llega ningún byte al cliente."""
    protocolo.enviar(cliente, json.dumps({"peticion": "pausa"}).encode())
    cliente.settimeout(0.3)
    with pytest.raises((socket.timeout, TimeoutError)):
        protocolo.recibir(cliente)


def test_peticion_pausa_alterna_estado(cliente, shared_data):
    assert shared_data["other"]["paused"] is False
    protocolo.enviar(cliente, json.dumps({"peticion": "pausa"}).encode())
    time.sleep(0.1)
    assert shared_data["other"]["paused"] is True


def test_peticion_desconocida_no_envia_respuesta(cliente):
    protocolo.enviar(cliente, json.dumps({"peticion": "xyz"}).encode())
    cliente.settimeout(0.3)
    with pytest.raises((socket.timeout, TimeoutError)):
        protocolo.recibir(cliente)


def test_json_invalido_no_rompe_servidor(cliente, shared_data, bot_position_dict):
    """JSON inválido no mata el servidor: la siguiente petición válida funciona."""
    protocolo.enviar(cliente, b"esto no es json{{{")
    time.sleep(0.05)
    respuesta = _enviar_peticion(cliente, {"peticion": "actualizacion"})
    assert respuesta["tipo"] == "actualizacion"


def test_multiples_peticiones_en_misma_conexion(cliente, bot_position_dict):
    for _ in range(5):
        respuesta = _enviar_peticion(cliente, {"peticion": "actualizacion"})
        assert respuesta["tipo"] == "actualizacion"


def test_reconexion_tras_cierre(servidor, shared_data, bot_position_dict):
    """Tras desconectar un cliente, el servidor acepta uno nuevo."""
    primer_cliente = socket.socket()
    primer_cliente.connect(("127.0.0.1", servidor))
    _enviar_peticion(primer_cliente, {"peticion": "actualizacion"})
    primer_cliente.close()
    time.sleep(0.1)

    segundo_cliente = socket.socket()
    segundo_cliente.connect(("127.0.0.1", servidor))
    respuesta = _enviar_peticion(segundo_cliente, {"peticion": "actualizacion"})
    assert respuesta["tipo"] == "actualizacion"
    segundo_cliente.close()
