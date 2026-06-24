# Services/Conexion_Visualizador/Salida_Datos/salida_bot.py

from Services.Serializaciones.bots import serializacion_completa_bot


def salida_bot_full(shared_data, entrada: dict) -> dict | None:
    bot = shared_data["bots"].get(entrada["id"])
    if bot is None:
        return None
    return serializacion_completa_bot(bot)
