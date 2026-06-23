# Services/Conexion_Visualizador/Salida_Datos/salida_dato.py

from Services.Conexion_Visualizador.Salida_Datos.salida_bot import salida_bot_full


def salida_dato(shared_data, entrada):
    serializacion = ""
    partes = []
    partes.append("{\n")
    partes.append('"tipo": "dato",')

    # Switch para determinar qué tipo de dato se está pidiendo
    #

    if entrada["entity"] == "bot":
        # Se pide detalles de un bot
        partes.append('"bot":' + salida_bot_full(shared_data, entrada))

    elif entrada["entity"] == "":
        # Se pide detalles de un ""
        partes.append('"":""')

    #
    ##########################################################

    partes.append("\n}<END>")
    serializacion = serializacion.join(partes)
    # print("mensaje para unity:\n" + serializacion)
    return serializacion
