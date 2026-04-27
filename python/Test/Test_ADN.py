import pytest
from typing import List, Union
from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.elementos import Genoma, Nodo
from Core.Entities.Elementos.Simples.Bot.ADN import empaquetador
from Core.Entities.Elementos.Simples.Bot.ADN.empaquetador import PackedDNA
import Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.base_gramatica as gramatica


@pytest.fixture
def crear_nodo_palabra_cf() -> List[Union[Nodo, Genoma]]:
    genoma = Genoma([0, 0, 2, 0, 0, 0, 5, 1])

    # declaramos
    nodo_palabra = gramatica._palabra()

    return [nodo_palabra, genoma]


# def test_generacion_codigo_palabra_cf(crear_nodo_palabra_cf):
#     nodo = crear_nodo_palabra_cf[0]
#     genoma = crear_nodo_palabra_cf[1]
#     compilado = nodo.compilar(genoma)
#     print("Codigo:")
#     print(compilado)
#     assert compilado == "cf"


# def test_pruebas(crear_nodo_palabra_cf: List[Union[Nodo, Genoma]]):


#     assert True
