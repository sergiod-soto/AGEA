import json
from Services.Conexion.SalidaActualizacion import salida_actualizacion
from Services.Conexion.SalidasDatos.SalidaDato import salida_dato
from Services.Conexion.SalidasDatos.SalidaMapa import salida_mapa
from Services.Conexion.SalidasDatos.SalidaPerfil import salida_perfil
from Utils.Sistema.Pause import pause


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
    )


def procesar_mensaje_salida(mensaje, shared_data):

    if mensaje["peticion"] == "actualizacion":
        return formatear(salida_actualizacion(shared_data)).encode()

    if mensaje["peticion"] == "dato":
        return formatear(salida_dato(shared_data, mensaje)).encode()

    if mensaje["peticion"] == "mapa":
        return formatear(salida_mapa(shared_data, mensaje)).encode()

    if mensaje["peticion"] == "perfil":
        return formatear(salida_perfil(shared_data, mensaje)).encode()

    if mensaje["peticion"] == "pausa":
        pause(shared_data)
        return "None"
