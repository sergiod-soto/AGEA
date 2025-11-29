from Core.Entities.Elementos.Simples.Bot.Bot import Bot


def serializar_bots(bots: dict[Bot]):

    serializacion = ""
    partes = []
    partes.append("[")

    for i, (id, bot) in enumerate(bots.items()):
        partes.append(bot.serialize_position())
        if i != len(bots) - 1:
            partes.append(",")
    partes.append("]")
    serializacion = serializacion.join(partes)

    return serializacion


def serializacion_completa_bot(bot: Bot):
    return bot.serialize_all()
