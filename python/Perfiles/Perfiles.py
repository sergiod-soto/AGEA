import json


def comprobar_perfil(perfil):
    perfiles = obtener_perfiles()
    for p in perfiles:
        if p == perfil:
            return True
    return False


def obtener_perfiles():
    with open("archivo.json", "r", encoding="utf-8") as f:
        perfiles = json.load(f)
        lista = []
        for perfil in perfiles:
            lista.append(perfil["id"])
        return lista

def cambiar_perfil(perfil):
    if comprobar_perfil(perfil):
        pass
