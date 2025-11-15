import json
from Utils.Sistema.Pause import pause


def receive_data(conn, shared_data):
    recibido = conn.recv(4096)
    if recibido:
        mensaje = recibido.decode(errors="ignore").strip()
        return procesar_mensaje(mensaje, shared_data)


def procesar_mensaje(mensaje, shared_data):

    msg = formatear(mensaje)
    print("[IMPORTER] Mensaje recibido:\n" + msg)
    try:
        msg = json.loads(msg) 
    except:
        print("[IMPORTER] Error al decodificar el mensaje JSON.")
        return
    if msg["tipo"] == "pause":
        pause(shared_data)


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
