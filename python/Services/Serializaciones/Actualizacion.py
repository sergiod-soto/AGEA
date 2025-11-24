from Services.Serializaciones.Mundo import serializar_mundo
from Services.Serializaciones.Bots import serializar_bots


def serializacion_actualizacion(shared_data):
    serializacion = ""
    partes = []
    partes.append("{\n")
    partes.append('"bots":' + serializar_bots(shared_data["bots"]))
    partes.append(",\n")
    partes.append('"mundo":' + serializar_mundo(shared_data["mundo"]))
    partes.append("\n}")
    serializacion = serializacion.join(partes)

    return serializacion
