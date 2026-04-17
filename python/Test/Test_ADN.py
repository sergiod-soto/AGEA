# test Core.Entities.Elemento.Simples.Bot.ADN.ADN.py

import pytest
from Core.Entities.Elementos.Simples.Bot.ADN.ADN import Genoma, Gen
from Core.Entities.Elementos.Simples.Bot.ADN import Empaquetador
from Core.Entities.Elementos.Simples.Bot.ADN.Empaquetador import generar
import Core.Entities.Elementos.Simples.Bot.ADN.Gramatica as Guia


# @pytest.fixture
# def crear_genoma_palabra_sd():
#     genoma = Genoma()

#     gen_palabra1 = Gen([0], "palabra")
#     gen_char1 = Gen([0, 0], "char")
#     gen_letra1 = Gen([0, 0, 0], "letra")
#     gen_palabra2 = Gen([0, 1], "palabra")
#     gen_char2 = Gen([0, 1, 0], "char")
#     gen_letra2 = Gen([0, 1, 0, 0], "letra")

#     genoma.add_gen(gen_palabra1)

#     gen_palabra1.add_elemento(gen_char1)
#     gen_palabra1.add_elemento(0)
#     gen_palabra1.add_elemento(gen_palabra2)

#     gen_char1.add_elemento(0)
#     gen_char1.add_elemento(gen_letra1)

#     gen_letra1.add_elemento(19)

#     gen_palabra2.add_elemento(gen_char2)
#     gen_palabra2.add_elemento(1)

#     gen_char2.add_elemento(0)
#     gen_char2.add_elemento(gen_letra2)

#     gen_letra2.add_elemento(3)

#     return genoma


# # def test_creacion_correcta_genoma(crear_genoma_palabra_sd):
# #     print("\n\n")

# #     # crear_genoma_palabra_sd["0"].print_gen()
# #     genoma = crear_genoma_palabra_sd
# #     for gen in genoma.genes:
# #         print(f"gen id: ({gen}),")
# #         print(f"\tprint: {genoma.genes[gen].print_gen()}")
# #         print(f"\tADN: {genoma.genes[gen].get_adn()}")
# #         print("\tGenerarOld:")
# #         print(Compiler.generarOld(
# #                 entrada=genoma.genes[gen].nombre,
# #                 tokens=0,
# #                 tokensArray=0,
# #                 adn = genoma.genes[gen].get_adn())
# #             )
# #         print(":" * 20)
# #         print()
# #     print("-" * 50)
# #     assert crear_genoma_palabra_sd.get_adn() == [0, 19, 0, 0, 3, 1]


# def test_pruebas(crear_genoma_palabra_sd):
#     genoma = crear_genoma_palabra_sd
#     gen = genoma.genes["0.1.0.0"]
#     adn_generado = generar(gen, Guia.guia)
#     print("ADN generado:")
#     print(adn_generado)

#     assert 1 == 1
