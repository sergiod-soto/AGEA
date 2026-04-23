from Services.Serializaciones.Bots import serializacion_completa_bot


def salida_bot_full(shared_data, entrada):
    bot = shared_data["bots"][entrada["id"]]
    return serializacion_completa_bot(bot)
