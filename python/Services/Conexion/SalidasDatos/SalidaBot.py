import socket
from Serializaciones.Bots import serializacion_completa_bot


def salida_bot(shared_data, entrada, conn: socket):
    bot = shared_data["bots"][entrada["id"]]
    conn.sendall(serializacion_completa_bot(bot).encode())
    return
