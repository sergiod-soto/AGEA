# Services/Conexion_Visualizador/procesado_salida_mensaje.py

import json

from Services.Conexion_Visualizador.salida_actualizacion import salida_actualizacion
from Services.Conexion_Visualizador.Salida_Datos.salida_dato import salida_dato
from Services.Conexion_Visualizador.Salida_Datos.salida_mapa import salida_mapa
from Services.Conexion_Visualizador.Salida_Datos.salida_perfil import salida_perfil
from Services.Conexion_Visualizador.Salida_Datos.salida_pause import salida_pause


def procesar_mensaje_salida(mensaje: dict, shared_data) -> bytes | None:
    """
    Despacha la petición entrante al handler correspondiente.

    Devuelve bytes con la respuesta serializada, o None si la petición
    es fire-and-forget (no requiere respuesta a Unity).

    Las respuestas son dicts Python serializados a JSON por este módulo,
    no por los handlers individuales. Los handlers devuelven dicts o None.
    """
    peticion = mensaje.get("peticion")

    if peticion == "actualizacion":
        respuesta = salida_actualizacion(shared_data)
    elif peticion == "dato":
        respuesta = salida_dato(shared_data, mensaje)
    elif peticion == "mapa":
        respuesta = salida_mapa(shared_data, mensaje)
    elif peticion == "perfil":
        respuesta = salida_perfil(shared_data, mensaje)
    elif peticion == "pausa":
        salida_pause(shared_data)
        return None
    else:
        print(f"[PROCESADO] Petición desconocida: {peticion!r}")
        return None

    if respuesta is None:
        return None

    return json.dumps(respuesta, ensure_ascii=False).encode()
