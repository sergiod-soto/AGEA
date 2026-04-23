import os


def guardar(dir, str):
    with open(dir, "w", encoding="utf-8") as f:
        f.write(str)


def guardar_hash_mascara(nombre, hash):
    """guardar como: "ejemplo.txt" """

    guardar(os.getcwd() + "/core/mundo/mascaras/hashes/" + nombre, hash)
