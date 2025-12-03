import json
from Services.Conexion.ProcesadoSalidaMensaje import procesar_mensaje_salida


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
        .replace("<END>\"", "")
    )


def receive_data(recibido, shared_data):

    if recibido:
        mensaje = recibido.decode(errors="ignore").strip()
        formateado = formatear(mensaje)
        formateado_json = json.loads(formateado)
        return procesar_mensaje_salida(formateado_json, shared_data)
