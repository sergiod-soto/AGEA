from Core.Entities.Elementos.Simples.Bot.Bot import Bot


def serializar_bots(bots: list[Bot]):

    serializacion = ""
    partes = []
    partes.append("[")
    for i, bot in enumerate(bots):
        partes.append(bot.serialize_position())
        if i != len(bots) - 1:  # última iteración
            partes.append(",")
    partes.append("]")
    serializacion = serializacion.join(partes)

    return serializacion


def serializacion_completa_bot(bot: Bot):
    return bot.serialize_all()
