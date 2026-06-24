# Test/Conexion_Visualizador/Unit/test_protocolo.py

import socket
import struct
import threading

import pytest

from Services.Conexion_Visualizador import protocolo


# ── helpers ───────────────────────────────────────────────────────────────────

def _par_sockets():
    """Devuelve (cliente, servidor) conectados localmente."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect(("127.0.0.1", port))
    servidor, _ = srv.accept()
    srv.close()
    return cliente, servidor


# ── enviar / recibir básico ───────────────────────────────────────────────────

def test_enviar_recibir_mensaje_simple():
    cliente, servidor = _par_sockets()
    payload = b"hola mundo"
    protocolo.enviar(cliente, payload)
    recibido = protocolo.recibir(servidor)
    assert recibido == payload
    cliente.close()
    servidor.close()


def test_enviar_recibir_mensaje_vacio():
    cliente, servidor = _par_sockets()
    protocolo.enviar(cliente, b"")
    recibido = protocolo.recibir(servidor)
    assert recibido == b""
    cliente.close()
    servidor.close()


def test_enviar_recibir_payload_grande():
    cliente, servidor = _par_sockets()
    payload = b"x" * 100_000
    protocolo.enviar(cliente, payload)
    recibido = protocolo.recibir(servidor)
    assert recibido == payload
    cliente.close()
    servidor.close()


def test_multiples_mensajes_en_secuencia():
    cliente, servidor = _par_sockets()
    mensajes = [b"primero", b"segundo", b"tercero"]
    for m in mensajes:
        protocolo.enviar(cliente, m)
    for m in mensajes:
        assert protocolo.recibir(servidor) == m
    cliente.close()
    servidor.close()


# ── cierre de conexión ────────────────────────────────────────────────────────

def test_recibir_devuelve_none_si_cliente_cierra():
    cliente, servidor = _par_sockets()
    cliente.close()
    resultado = protocolo.recibir(servidor)
    assert resultado is None
    servidor.close()


def test_recibir_devuelve_none_si_cierra_tras_cabecera_parcial():
    """Cierre a mitad de la cabecera → None, sin excepción."""
    cliente, servidor = _par_sockets()
    # envía solo 2 de los 4 bytes de cabecera y cierra
    cliente.send(struct.pack(">H", 0))
    cliente.close()
    resultado = protocolo.recibir(servidor)
    assert resultado is None
    servidor.close()


def test_recibir_devuelve_none_si_cierra_tras_cabecera_completa():
    """Cabecera indica N bytes pero llegan 0 → None."""
    cliente, servidor = _par_sockets()
    # cabecera dice que vienen 10 bytes, luego cierra sin enviarlos
    cliente.send(struct.pack(">I", 10))
    cliente.close()
    resultado = protocolo.recibir(servidor)
    assert resultado is None
    servidor.close()


# ── framing correcto ──────────────────────────────────────────────────────────

def test_cabecera_contiene_longitud_correcta():
    cliente, servidor = _par_sockets()
    payload = b"test"

    recibido_raw = []

    def _leer():
        # leemos los bytes crudos sin usar protocolo.recibir
        buf = b""
        while len(buf) < 4 + len(payload):
            buf += servidor.recv(1024)
        recibido_raw.append(buf)

    t = threading.Thread(target=_leer)
    t.start()
    protocolo.enviar(cliente, payload)
    t.join()

    longitud = struct.unpack(">I", recibido_raw[0][:4])[0]
    assert longitud == len(payload)
    assert recibido_raw[0][4:] == payload

    cliente.close()
    servidor.close()
