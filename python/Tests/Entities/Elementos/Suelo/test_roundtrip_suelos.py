# Tests/Entities/Elementos/Suelo/test_roundtrip_suelos.py
"""
Ida y vuelta de cada suelo: serializar -> reconstruir -> serializar debe dar el
MISMO dict. Detecta campos que no viajan (la guarda de Elemento.serializar) y
datos que se pierden al reconstruir (Sector y Logica reconstruyen con __new__,
sin __init__). Imprime el tamaño para estimar el mensaje gRPC de un Sector.
"""
import json

import pytest

from Core.Entities.Elementos.registry import ELEMENTOS, reconstruir_elemento

SUELOS = [
    "Suelo_Piedra", "Suelo_Arena", "Suelo_Grava", "Suelo_Hielo",
    "Suelo_Oceano", "Suelo_Tierra", "Suelo_Barro", "Suelo_Cesped",
]


@pytest.mark.parametrize("nombre", SUELOS)
def test_roundtrip(nombre):
    # Argumentos con nombre: los suelos no comparten el orden del constructor.
    suelo = ELEMENTOS[nombre](casilla=(3, 4), id_elemento=7)
    antes = suelo.serializar()
    # json.dumps: lo que viaja de verdad (falla si algo no es serializable).
    blob = json.dumps(antes)
    despues = reconstruir_elemento(json.loads(blob)).serializar()
    assert despues == antes
    print(f"{nombre}: {len(blob.encode())} bytes -> {len(blob.encode()) * 1600 / 1e6:.2f} MB por Sector")