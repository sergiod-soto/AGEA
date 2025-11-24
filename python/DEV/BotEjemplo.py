import sys
import os
from Core.Entities.Elementos.Bot import AdnFile
from Core.Entities.Elementos.Bot.Funciones import Formater, GuiaParser

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


tokens = GuiaParser.guia
tokensArray = GuiaParser.guiaArray


def main(genoma):

    adn = AdnFile.AdnClass(genoma)
    codigo = Formater.generar("programa", tokens, tokensArray, adn)

    #
    #
    print(
        "\n\n\nCódigo:\n\n--- INICIO PROGRAMA ---\n\n"
        + codigo
        + "\n\n--- FIN PROGRAMA ---\n\n"
    )
    #
    #


genoma = [1, 1, 1, 1, 1]
main(genoma)
