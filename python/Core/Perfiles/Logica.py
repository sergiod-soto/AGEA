import json
import os


"""
Docstring for Core.Logica.Perfiles.Logica

Logica de los perfiles.

Gestion de comprobacion de mascaras y datos del mundo.
"""


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

    with open(
        ruta_base + "/Services/Perfiles/Perfiles.json", "r", encoding="utf-8"
    ) as f:
        return json.load(f)
       
def cambiar_perfil(perfil):
    if _comprobar_perfil(perfil):
        pass
    raise NotImplementedError("Core.Perfiles.Logica.cambiar_perfil()")