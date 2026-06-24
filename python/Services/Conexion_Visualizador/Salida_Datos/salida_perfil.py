# Services/Conexion_Visualizador/Salida_Datos/salida_perfil.py

from Config import settings
from Utils.Ficheros.leer_json import leer_JSON_Datos


def salida_perfil(shared_data, mensaje: dict) -> dict | None:
    tipo = mensaje.get("tipo")

    if tipo == "obtener_perfiles":
        return _obtener_perfiles()

    print(f"[SALIDA_PERFIL] Tipo desconocido: {tipo!r}")
    return None


def _obtener_perfiles() -> dict:
    perfiles = []
    for num in range(1, settings.NUM_PERFILES + 1):
        perfil = _obtener_perfil(num)
        if perfil is not None:
            perfiles.append(perfil)

    return {
        "peticion": "perfil",
        "tipo": "obtener_perfiles",
        "perfiles": perfiles,
    }


def _obtener_perfil(perfil_num: int) -> dict | None:
    try:
        perfil = leer_JSON_Datos(perfil_num)
    except Exception as e:
        print(f"[SALIDA_PERFIL] Error leyendo perfil {perfil_num}: {e}")
        return None

    return {
        "id": perfil["id"],
        "nombre": perfil["nombre"],
        "fecha": perfil["fecha"],
        "tiempo_entrenamiento": perfil["tiempo_entrenamiento"],
    }
