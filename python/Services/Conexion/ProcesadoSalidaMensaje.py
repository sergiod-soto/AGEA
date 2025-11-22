import socket
import json
from Conexion.SalidasDatos.SalidaDato import salida_dato
from Serializaciones.Actualizacion import serializacion_actualizacion


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
        conn.sendall(serializacion_actualizacion(shared_data).encode())
        return

    if mensaje["tipo"] == "dato":
        salida_dato(shared_data, entrada, conn)
