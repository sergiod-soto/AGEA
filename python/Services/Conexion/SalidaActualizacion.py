from socket import socket
from Serializaciones.Actualizacion import serializacion_actualizacion


def salida_actualizacion(shared_data, conn: socket):
    conn.sendall(serializacion_actualizacion(shared_data).encode())
