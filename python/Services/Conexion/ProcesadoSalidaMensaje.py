import json
from Services.Conexion.SalidaActualizacion import salida_actualizacion
from Services.Conexion.SalidasDatos.SalidaDato import salida_dato


def formatear(texto: str) -> str:
    return (
        texto.replace("\\n", "")
        .replace("\\r", "")
        .replace("'", '"')
        .replace('"{', "{")
        .replace('}"', "}")
        .replace('"[', "[")
        .replace(']"', "]")
        .replace("\\", "")
        .replace("<END>", "")
    )


def procesar_mensaje_salida(mensaje, shared_data):

    if mensaje["tipo"] == "actualizacion":
        return salida_actualizacion(shared_data).encode()

    if mensaje["tipo"] == "dato":
        return salida_dato(shared_data, mensaje).encode()
