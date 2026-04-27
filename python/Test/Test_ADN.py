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
            print("\t\t" + str(i) + "." + str(j) + " - " + sub_h.get_nombre())
            j += 1
        
    nodo_char = hijos[0]
    
    print("\nHijo " + nodo_char.get_nombre() + ":")
    print("Numero de hijos: " + str(len(nodo_char.get_hijos())))
    i = 0
    for hijo in nodo_char.get_hijos():
        print("\t" + str(i) + " - " + hijo.get_nombre())
        
    print("\n\nOFFSETS")
    print("nodo _palabra:")
    offset_palabra = nodo.get_offsets()
    print("\t" + str(offset_palabra[0]) + ", " + str(offset_palabra[1]))
    print("nodo _char:")
    nodo_char = nodo.get_hijos()[0]
    offset_char = nodo_char.get_offsets()
    print("\t" + str(offset_char[0]) + ", " + str(offset_char[1]))
    print("nodo _letra:")
    nodo_letra = nodo_char.get_hijos()[0]
    offset_letra = nodo_letra.get_offsets()
    print("\t" + str(offset_letra[0]) + ", " + str(offset_letra[1]))
    print("nodo _minuscula:")
    nodo_minuscula = nodo_letra.get_hijos()[0]
    offset_minuscula = nodo_minuscula.get_offsets()
    print("\t" + str(offset_minuscula[0]) + ", " + str(offset_minuscula[1]))
    print("nodo _palabra2:")
    nodo_palabra2 = nodo.get_hijos()[1]
    offset_palabra2 = nodo_palabra2.get_offsets()
    print("\t" + str(offset_palabra2[0]) + ", " + str(offset_palabra2[1]))

    assert True
