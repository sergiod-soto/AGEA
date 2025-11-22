import socket
import json
from Conexion.SalidaActualizacion import salida_actualizacion
from Conexion.SalidasDatos.SalidaDato import salida_dato


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


def procesar_mensaje_salida(mensaje, shared_data, conn: socket):

    entrada = formatear(mensaje)
    try:
        entrada = json.loads(entrada)
    except:
        # [print:exception]
        print("[IMPORTER] Error al decodificar el mensaje JSON.")
        return

    if mensaje["tipo"] == "actualizacion":
        salida_actualizacion(shared_data, conn)
        return

    if mensaje["tipo"] == "dato":
        salida_dato(shared_data, entrada, conn)
        return
