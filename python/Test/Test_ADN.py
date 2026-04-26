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


def test_generacion_codigo_palabra_cf(crear_nodo_palabra_cf):
    nodo = crear_nodo_palabra_cf[0]
    genoma = crear_nodo_palabra_cf[1]
    compilado = nodo.compilar(genoma)
    print("Codigo:")
    print(compilado)
    assert compilado == "cf"


def test_pruebas(crear_nodo_palabra_cf: List[Union[Nodo, Genoma]]):
    nodo = crear_nodo_palabra_cf[0]
    genoma = crear_nodo_palabra_cf[1]
    compilado = nodo.compilar(genoma)
    
    hijos = nodo.get_hijos()
    print("Nodo principal:\n")
    print(nodo.get_nombre())
    i = 0
    for hijo in hijos:
        print("\t" + str(i) + " - " + hijo.get_nombre())
        i += 1
        subhijos = hijo.get_hijos()
        j = 0
        print("hijos de " + str(hijo.get_nombre() + ": (" + str(len(hijo.get_hijos())) + ")"))
        for sub_h in subhijos:
            print("\t\t" + str(i) + "." + str(j) + "- " + sub_h.get_nombre())
            j += 1

    assert True
