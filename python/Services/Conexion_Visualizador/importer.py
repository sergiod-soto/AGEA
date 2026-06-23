# Services/Conexion_Visualizador/importer.py

import json
from Services.Conexion_Visualizador.procesado_salida_mensaje import procesar_mensaje_salida


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
        #.replace('<END>"', "")
    )


def receive_data(recibido, shared_data):

    if recibido:
        mensaje = recibido.decode(errors="ignore").strip()
        
        # deberia cambiarlo. ahora mismo, si llegan varias peticiones, solo le hago caso a la 1ª
        mensaje = mensaje.split("<END>")[0] 
        formateado = formatear(mensaje)

        formateado_json = json.loads(formateado)
        return procesar_mensaje_salida(formateado_json, shared_data)
