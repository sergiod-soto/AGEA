from Services.Conexion.SalidasDatos.SalidaBot import salida_bot_full


def salida_dato(shared_data, entrada):
    serializacion = ""
    partes = []
    partes.append("{\n")
    partes.append('"tipo": "actualizacion"')

    if entrada["entity"] == "bot":
        # Se pide detalles de un bot
        partes.append('"bot":' + salida_bot_full(shared_data, entrada))

    partes.append("\n}<END>")
    serializacion = serializacion.join(partes)
    return serializacion
