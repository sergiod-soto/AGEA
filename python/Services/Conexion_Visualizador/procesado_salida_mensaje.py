import json
from Services.Conexion_Visualizador.salida_actualizacion import salida_actualizacion
from Services.Conexion_Visualizador.SalidasDatos.salida_dato import salida_dato
from Services.Conexion_Visualizador.SalidasDatos.salida_mapa import salida_mapa
from Services.Conexion_Visualizador.SalidasDatos.salida_perfil import salida_perfil
from Utils.Sistema.pause import pause
from Dev import consola_dev


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

    elif mensaje["peticion"] == "dato":
        return formatear(salida_dato(shared_data, mensaje)).encode()

    elif mensaje["peticion"] == "mapa":
        return formatear(salida_mapa(shared_data, mensaje)).encode()

    elif mensaje["peticion"] == "perfil":
        return formatear(salida_perfil(shared_data, mensaje)).encode()

    elif mensaje["peticion"] == "consola_dev":
        consola_dev.abrir_consola(shared_data["mundo"])
        return "None"

    elif mensaje["peticion"] == "pausa":
        pause(shared_data)
        return "None"
