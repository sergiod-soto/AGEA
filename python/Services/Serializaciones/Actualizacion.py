# Services/Serializaciones/actualizacion.py

from Services.Serializaciones.bots import serializar_bots
from Services.Serializaciones.mundo import serializar_mundo


def serializacion_actualizacion(shared_data) -> dict:
    return {
        "tipo": "actualizacion",
        "bots": serializar_bots(shared_data["bots"]),
        "mundo": serializar_mundo(shared_data["mundo"]),
    }