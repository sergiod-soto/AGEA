import json
import os


"""
Docstring for Core.Logica.Perfiles.Logica

Logica de los perfiles.

Gestion de comprobacion de mascaras y datos del mundo.
"""


directorio_perfiles = "/Services/Perfiles/Perfiles.json"


def _comprobar_perfil(perfil):
    perfiles = _obtener_perfiles()
    for p in perfiles:
        if p == perfil:
            return True
    return False


def _obtener_perfiles():
    ruta_base = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    with open(ruta_base + directorio_perfiles, "r", encoding="utf-8") as f:
        return json.load(f)["id"]


def cambiar_perfil_activo(perfil):
    if _comprobar_perfil(perfil):
        pass
    raise NotImplementedError("Core.Perfiles.Logica.cambiar_perfil_activo()")


def obtener_datos_perfil(perfil):
    ruta_base = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    with open(
        ruta_base + "/Services/Perfiles/" + perfil + "/Datos.json",
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def obtener_datos_todos_perfiles():
    perfiles = _obtener_perfiles()
    datos = []
    for perfil in perfiles:
        datos.append(obtener_datos_perfil(perfil))
    return datos


def cambiar_nombre_perfil(perfil, nuevo_nombre):

    if not _comprobar_perfil(perfil):
        raise ValueError("No existe perfil con el nombre de " + perfil)

    ruta_base = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    datos = None
    with open(ruta_base + directorio_perfiles, "r", encoding="utf-8") as f:
        datos = json.load(f)

    if datos == None:
        raise ValueError("No se han podido cargar los datos de los perfiles")

    nombres = datos["id"]

    for nombre in nombres:
        if nombre == perfil:
            nombre = nuevo_nombre

    datos["id"] = nombres

    with open(ruta_base + directorio_perfiles, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
