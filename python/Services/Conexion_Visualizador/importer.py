# Services/Conexion_Visualizador/importer.py

import json

from Services.Conexion_Visualizador.procesado_salida_mensaje import (
    procesar_mensaje_salida,
)


def receive_data(recibido: bytes, shared_data) -> bytes | None:
    mensaje_str = recibido.decode(errors="ignore").strip()

    try:
        mensaje = json.loads(mensaje_str)
    except json.JSONDecodeError as e:
        print(f"[IMPORTER] JSON inválido: {e}\nEntrada: {mensaje_str!r}")
        return None

    return procesar_mensaje_salida(mensaje, shared_data)
