import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import Funcionalidades.Bots.Formater as Formater
import Funcionalidades.Bots.GuiaParser as GuiaParser
import Elementos.Bot.AdnFile as AdnFile

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
