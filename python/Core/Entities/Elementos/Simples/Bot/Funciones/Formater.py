#####################################################
#####################################################


#
#
#
def generar(entrada, tokens, tokensArray, adn):
    """
    funcion auxiliar para la recursividad de generar codigo
    """

    generado = ""
    numTabs = 0

    def generarAux(tokenBase, tokens, tokensArray, adn):

        def imprimirTabs(numTabs):
            nonlocal generado
            for _ in range(numTabs):
                generado += "\t"
            return generado

        nonlocal generado
        nonlocal numTabs

        modoEleccion = False

        if tokenBase in tokensArray:
            seccion = tokens[tokensArray[tokenBase]]
        else:
            seccion = [tokenBase]

        # recorro el array
        for i in range(len(seccion)):
            #
            #
            if modoEleccion:
                modoEleccion = False
                if isinstance(seccion[i], list):
                    #
                    # me he encontrado un \e y ahora un array
                    #
                    # almaceno el ultimo elemento del adn y lo elimino
                    cromosoma = adn.next_chromosome()

                    #
                    # ahora toca generar la eleccion:
                    #
                    # elijo el array correspondiente con tokens[i][cromosoma]
                    # y lo genero entero
                    if cromosoma >= len(seccion[i]):
                        raise Exception(
                            f"Encontrado cromosoma [{cromosoma}] mayor al numero de opciones [{len(seccion[i]) - 1}]"
                        )
                    for k in range(len(seccion[i][cromosoma])):
                        generarAux(seccion[i][cromosoma][k], tokens, tokensArray, adn)
                else:
                    raise Exception(
                        f"No encontrado Array tras '\\e' en linea {i} de {seccion[i]}, en modo eleccion"
                    )

            #
            #
            elif seccion[i] == "":
                pass

            #
            #
            elif seccion[i] in tokensArray:
                generarAux(seccion[i], tokens, tokensArray, adn)

            #
            #
            elif seccion[i][0] == "\\":
                if seccion[i][1] == "n":
                    generado += "\n"
                elif seccion[i][1] == "t":
                    numTabs += 1
                elif seccion[i][1] == "r":
                    numTabs -= 1
                elif seccion[i][1] == "e":
                    modoEleccion = True
                elif seccion[i][1] == ":":
                    pass
                else:
                    # no deberia haber \texto -> se lanza excepcion
                    raise Exception(
                        f"Encontrado '\\texto' en linea {i} de {seccion[i]}"
                    )

            #
            #
            else:
                imprimirTabs(numTabs)
                generado += seccion[i]

    generarAux(entrada, tokens, tokensArray, adn)

    return generado


#
#
#
#
#
################################################
