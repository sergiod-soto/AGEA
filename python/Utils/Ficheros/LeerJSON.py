from pathlib import Path


def leer_JSON_Datos(id_perfil):

    import json

    raiz = Path(__file__).resolve().parents[2]
    ruta_json = raiz / "Services" / "Perfiles" / f"Perfil{id_perfil}" / "Datos.json"

    with open(ruta_json, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    return datos
