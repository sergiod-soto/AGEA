# Services/Conexion_Visualizador/protocolo.py
#
# Framing length-prefix: cada mensaje va precedido de 4 bytes (big-endian)
# que indican la longitud del payload en bytes.
#
#   [4 bytes longitud] [N bytes payload]
#
# Esto garantiza que mensajes grandes o partidos en varios paquetes TCP
# se reensamblan correctamente, sin depender de delimitadores en los datos.

import struct
import socket

_HEADER = 4  # bytes del prefijo de longitud
_FORMAT = ">I"  # unsigned int, big-endian


def enviar(conn: socket.socket, datos: bytes) -> None:
    """Envía datos con framing length-prefix."""
    cabecera = struct.pack(_FORMAT, len(datos))
    conn.sendall(cabecera + datos)


def recibir(conn: socket.socket) -> bytes | None:
    """
    Recibe un mensaje completo con framing length-prefix.
    Devuelve los bytes del payload, o None si el cliente cerró la conexión.
    """
    cabecera = _recibir_exacto(conn, _HEADER)
    if cabecera is None:
        return None

    longitud = struct.unpack(_FORMAT, cabecera)[0]
    return _recibir_exacto(conn, longitud)


def _recibir_exacto(conn: socket.socket, n: int) -> bytes | None:
    """
    Lee exactamente n bytes del socket.
    Devuelve None si el cliente cerró la conexión antes de completarlos.
    """
    buffer = b""
    while len(buffer) < n:
        fragmento = conn.recv(n - len(buffer))
        if not fragmento:
            return None
        buffer += fragmento
    return buffer
