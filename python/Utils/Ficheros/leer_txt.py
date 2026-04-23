import os


def leer(dir):
    with open(dir, "r", encoding="utf-8") as f:
        return f.read()


def leer_hash_mascara(nombre):
    """buscar como: "ejemplo.txt" """

    return leer(os.getcwd() + "/core/mundo/mascaras/hashes/" + nombre)