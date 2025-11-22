import socket
from Conexion.SalidasDatos.SalidaBot import salida_bot_full


def salida_dato(shared_data, entrada):
    if entrada["entity"] == "bot":
        # Se pide detalles de un bot
        return salida_bot_full(shared_data, entrada)
        
