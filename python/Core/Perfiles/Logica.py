import json
import os


"""
Docstring for Core.Logica.Perfiles.Logica

Logica de los perfiles.

Gestion de comprobacion de mascaras y datos del mundo.
"""


directorio_perfiles = "/Services/Perfiles"
ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _comprobar_perfil(perfil):
    perfiles = obtener_datos_perfiles()
    for perfil in perfiles:
        if perfil["nombre"] == perfil:
            return True
    return False


def _extraer_datos_perfil_desde_json(json):
    return {"nombre": json["nombre"], "fecha": json["fecha"]}


# TODO cambiar
def cambiar_perfil_activo(perfil):
    if _comprobar_perfil(perfil):
        pass
    raise NotImplementedError("Core.Perfiles.Logica.cambiar_perfil_activo()")


def obtener_datos_perfiles():
    perfiles = []
    for i in range(1, 6):
        with open(
            ruta_base + "/Services/Perfiles/Perfil" + str(i) + "/Datos.json",
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)
            perfiles.append(_extraer_datos_perfil_desde_json(data))
    return perfiles


def cambiar_nombre_perfil(perfil, nuevo_nombre):
    """
    Docstring for cambiar_nombre_perfil

    :param perfil: id del perfil, no el nombre
    :param nuevo_nombre: nuevo nombre
    """

    if not _comprobar_perfil(perfil):
        raise ValueError("No existe perfil con el nombre de " + perfil)

    datos = None
    with open(ruta_base + directorio_perfiles + perfil + "/Datos.json", "r", encoding="utf-8") as f:
        datos = json.load(f)

    if datos == None:
        raise ValueError("No se han podido cargar los datos de los perfiles")

    datos["nombre"] = nuevo_nombre

    with open(ruta_base + directorio_perfiles + perfil + "/Datos.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
