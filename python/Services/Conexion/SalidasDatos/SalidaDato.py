import socket
from Conexion.SalidasDatos.SalidaBot import salida_bot


def salida_dato(shared_data, entrada, conn: socket):
    if entrada["entity"] == "bot":
        # Se pide detalles de un bot
        salida_bot(shared_data, entrada, conn)
        return
