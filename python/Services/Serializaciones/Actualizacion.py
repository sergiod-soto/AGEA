# Services/Conexion_Visualizador/Serializaciones/actualizacion.py

from Serializaciones.mundo import serializar_mundo
from Services.Serializaciones.bots import serializar_bots


def serializacion_actualizacion(shared_data):
    serializacion = ""
    partes = []
    partes.append("{\n")
    partes.append('"tipo": "actualizacion",\n')
    partes.append('"bots":' + serializar_bots(shared_data["bots"]) + ",\n")
    partes.append('"mundo":' + serializar_mundo(shared_data["mundo"]) + "\n")
    partes.append("}<END>")
    serializacion = serializacion.join(partes)
    return serializacion
