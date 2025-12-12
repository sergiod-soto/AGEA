import json
from Services.Conexion.SalidaActualizacion import salida_actualizacion
from Services.Conexion.SalidasDatos.SalidaDato import salida_dato
from Services.Conexion.SalidasDatos.SalidaMapa import salida_mapa
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

    if mensaje["tipo"] == "actualizacion":
        a = formatear(salida_actualizacion(shared_data))
        return a.encode()

    if mensaje["tipo"] == "dato":
        return formatear(salida_dato(shared_data, mensaje)).encode()
    
    if mensaje["tipo"] == "mapa":
        return formatear(salida_mapa(shared_data, mensaje)).encode()
    
    if mensaje["tipo"] == "perfil":
        
        return "None"

    if mensaje["tipo"] == "pausa":
        pause(shared_data)
        return "None"
