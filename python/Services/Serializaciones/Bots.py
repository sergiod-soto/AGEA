# Services/Serializaciones/bots.py

from Core.Entities.Elementos.Simples.Bot.Bot import Bot


def serializar_bots(bots: dict) -> list:
    """
    Serializa todos los bots a una lista de dicts con su posición.
    bots: dict {id: Bot}
    """
    return [bot.serialize_position() for bot in bots.values()]


def serializacion_completa_bot(bot: Bot) -> dict:
    return bot.serialize_all()
