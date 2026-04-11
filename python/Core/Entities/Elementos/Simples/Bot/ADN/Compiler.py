#####################################################
#####################################################
from Core.Entities.Elementos.Simples.Bot.ADN.ADN import ADN_Lineal, Genoma, Gen


#
#
#
def generarOld(entrada, tokens, tokensArray, adn):
    """
    funcion auxiliar para la recursividad de generar codigo
    """

    generado = ""
    partes = []
    numTabs = 0

    def generarAux(tokenBase, tokens, tokensArray, adn: ADN_Lineal):

        def imprimirTabs(numTabs):
            nonlocal generado
            for _ in range(numTabs):
                partes.append("\t")
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
            elif seccion[i] == "":
                pass
            elif seccion[i] in tokensArray:
                generarAux(seccion[i], tokens, tokensArray, adn)
            elif seccion[i][0] == "\\":
                if seccion[i][1] == "n":
                    partes.append("\n")
                elif seccion[i][1] == "t":
                    numTabs += 1
                elif seccion[i][1] == "r":
                    numTabs -= 1
                elif seccion[i][1] == "e":
                    modoEleccion = True
                elif seccion[i][1] == "x":
                    continue
                else:
                    # no deberia haber \texto -> se lanza excepcion
                    raise Exception(
                        f"Encontrado '\\texto' en linea {i} de {seccion[i]}"
                    )
            else:
                imprimirTabs(numTabs)
                partes.append(seccion[i])

    generarAux(entrada, tokens, tokensArray, adn)

    return generado.join(partes)


def compilar(gen: Gen):
    """
    genera codigo a partir de un gen.
    'compilar' es compilar_nodo(), pero
    sirviendo como punto de entrada general
    inicializando los non local
    """

    generado = ""
    partes = []
    numTabs = 0
    modo_eleccion = False

    adn = gen.get_adn()

    ite_adn = 0

    def anhadir_tabs(codigo):
        generado_anhadir_tabs = ""
        partes_anhadir_tabs = []

        for _ in range(numTabs):
            partes_anhadir_tabs.append("\\t")
        partes_anhadir_tabs.append(codigo)

        return generado_anhadir_tabs.join(partes_anhadir_tabs)

    def digerir_comando(token):
        nonlocal modo_eleccion

        comando = token[1]

        a_retornar = ""
        a_retornar_partes = []

        if comando == "e":
            modo_eleccion = True
        elif comando == "t":
            numTabs += 1
        elif comando == "n":
            a_retornar_partes.append("\n")
        elif comando == "x":
            a_retornar_partes.append("")
        elif comando == "\\":
            a_retornar_partes.append("\\")
        else:
            raise Exception(f"Comando no reconocido ({comando})")

        # compruebo el resto del token (caso ej: {\tcodigo})
        if len(token) > 2:
            if comando != "t" and comando != "\\":
                raise Exception(
                    "Solo los comandos '\\\\' y '\\t' pueden tener mas contenido."
                )
            a_retornar_partes.append(compilar_token(token[2:]))
        return a_retornar.join(a_retornar_partes)

    def compilar_eleccion(token):
        nonlocal modo_eleccion

        modo_eleccion = False
        return compilar_token(token)

    def compilar_array(array):
        partes_compilar_array = []
        for token in array:
            partes_compilar_array.append(compilar_token(token))
        return partes_compilar_array

    def compilar_nodo(nodo: Gen):
        partes = ""
        compilado_partes = []

        for elemento in nodo.guia:
            print("elemento: " + str(elemento))
            compilado_partes.append(compilar_token(elemento))
        return partes.join(compilado_partes)

    def compilar_token(token):
        """
        token puede ser comando, string o nodo
        """

        nonlocal ite_adn
        nonlocal modo_eleccion

        if isinstance(token, list):
            """
            Nos encontramos un array:
            lo compilamos como conjunto de tokens o
            como uno solo depende de si estamos en modo eleccion
            """
            if modo_eleccion is True:
                modo_eleccion = False
                aux_adn = adn[ite_adn]
                ite_adn += 1
                return compilar_eleccion(aux_adn)
            else:
                return compilar_array(token)

        """
        Nos encontramos un string.
        puede ser un comando, un nodo o nada 
        y entonces es un string
        """
        if modo_eleccion is True:
            if es_comando(token):
                raise Exception("Encontrado comando en eleccion")
            if es_nodo(token):
                raise Exception("Encontrado nodo en eleccion")
            raise Exception("Encontrado string en eleccion")

        if es_nodo(token):
            aux1 = compilar_nodo(token)
            aux2 = anhadir_tabs(aux1)
            return aux2

        if es_comando(token):
            return anhadir_tabs(digerir_comando(token))

        # No es nada de lo anterior, por lo que es texto sin significado
        return token

    def es_comando(token):
        if isinstance(token, str) is False:
            return False
        if token[0] == "\\":
            return True
        return False

    def es_nodo(token):
        if isinstance(token, Gen):
            return True
        return False

    partes.append(compilar_nodo(gen))
    return generado.join(partes)


##################################################################
##################################################################


def anhadir_tabs_TEST(codigo, numTabs):
    generado_anhadir_tabs = ""
    partes_anhadir_tabs = []

    for _ in range(numTabs):
        partes_anhadir_tabs.append("\\t")
    partes_anhadir_tabs.append(codigo)

    return generado_anhadir_tabs.join(partes_anhadir_tabs)


def es_comando_TEST(token):
    if isinstance(token, str) and token[0] == "\\":
        return True
    return False


def es_nodo_TEST(token):
    if isinstance(token, Gen):
        return True
    return False


# depende: compilar_token_TEST
def digerir_comando_TEST(token, numTabs):

    comando = token[1]

    a_retornar = ""
    a_retornar_partes = []

    if comando == "e":
        pass
    elif comando == "t":
        numTabs += 1
    elif comando == "n":
        a_retornar_partes.append("\n")
    elif comando == "x":
        a_retornar_partes.append("")
    elif comando == "\\":
        a_retornar_partes.append("\\")
    else:
        raise Exception(f"Comando no reconocido ({comando})")

    # compruebo el resto del token (caso ej: {\tcodigo})
    if len(token) > 2:
        if comando != "t" and comando != "\\":
            raise Exception(
                "Solo los comandos '\\\\' y '\\t' pueden tener mas contenido."
            )
        print("Se va a compilar_token de: " + str(token[2:]))
        a_retornar_partes.append(compilar_token_TEST(token[2:]))
    numTabs -= 1
    return a_retornar.join(a_retornar_partes)


# depende: compilar_token_TEST
def compilar_eleccion_TEST(token):
    return compilar_token_TEST(token)


# depende: compilar_token_TEST
def compilar_array_TEST(array):
    partes_compilar_array = []
    for token in array:
        partes_compilar_array.append(compilar_token_TEST(token))
    return partes_compilar_array


# depende: compilar_token_TEST
def compilar_nodo_TEST(nodo: Gen):
    partes = ""
    compilado_partes = []
    adn = nodo.get_adn()
    iterador = 0
    guia = nodo.guia

    for elemento in guia:
        compilado_partes.append(
            compilar_token_TEST(
                elemento,
                iterador,
            )
        )

    return partes.join(compilado_partes)


# depende:
#
# compilar_eleccion_TEST
# compilar_array_TEST
# es_comando_TEST
# es_nodo_TEST
# compilar_nodo_TEST
def compilar_token_TEST(token, ite_adn, modo_eleccion, adn):
    """
    token puede ser comando, string o nodo
    """

    if isinstance(token, list):
        """
        Nos encontramos un array:
        lo compilamos como conjunto de tokens o
        como uno solo depende de si estamos en modo eleccion
        """
        if modo_eleccion:
            modo_eleccion = False
            aux_adn = adn[ite_adn]
            ite_adn += 1
            return compilar_eleccion_TEST(aux_adn)
        else:
            return compilar_array_TEST(token)

    """
    Nos encontramos un string.
    puede ser un comando, un nodo o nada 
    y entonces es un string
    """
    if modo_eleccion is True:
        if es_comando_TEST(token):
            raise Exception("Encontrado comando en eleccion")
        if es_nodo_TEST(token):
            raise Exception("Encontrado nodo en eleccion")
        raise Exception("Encontrado string en eleccion")

    if es_nodo_TEST(token):
        aux1 = compilar_nodo_TEST(token)
        aux2 = anhadir_tabs_TEST(aux1)
        return aux2

    if es_comando_TEST(token):
        return anhadir_tabs_TEST(digerir_comando_TEST(token))

    # No es nada de lo anterior, por lo que es texto sin significado
    return token


genoma = Genoma()

gen_palabra1 = Gen([0], "palabra")
gen_char1 = Gen([0, 0], "char")
gen_letra1 = Gen([0, 0, 0], "letra")
gen_palabra2 = Gen([0, 1], "palabra")
gen_char2 = Gen([0, 1, 0], "char")
gen_letra2 = Gen([0, 1, 0, 0], "letra")

genoma.add_gen(gen_palabra1)
gen_palabra1.add_elemento(gen_char1)
gen_palabra1.add_elemento(0)
gen_palabra1.add_elemento(gen_palabra2)
gen_char1.add_elemento(0)
gen_char1.add_elemento(gen_letra1)
gen_letra1.add_elemento(19)
gen_palabra2.add_elemento(gen_char2)
gen_palabra2.add_elemento(1)
gen_char2.add_elemento(0)
gen_char2.add_elemento(gen_letra2)
gen_letra2.add_elemento(3)


def compiler_test():
    print("-" * 25)
    print("\tComenzando Test:\n")

    # test_es_comando_TEST()        #   ok
    # test_anhadir_tabs_TEST()      #   ok
    # test_es_comando_TEST()        #   ok
    # test_anhadir_tabs_TEST()      #   ok
    # test_digerir_comando_TEST()   #   -   falta por comprobar de nuevo cuando compilar_token_TEST sea ok  -
    print("compilar(gen_letra2):")
    print(compilar(gen_letra2))

    print("-" * 25)


def test_es_nodo_TEST():
    print("--- es_nodo_TEST()")
    print(f"Nodo 1: gen_palabra1, nodo 2: '0'")
    print("1) " + str(es_nodo_TEST(gen_palabra1)) + ", 2) " + str(es_nodo_TEST(0)))
    print()


def test_anhadir_tabs_TEST():
    print("--- anhadir_tabs_TEST()")
    print(
        "1 tab:\n"
        + str(anhadir_tabs_TEST("codigo_test", 1))
        + "\n\n3 tabs:\n"
        + str(anhadir_tabs_TEST("codigo_test", 3))
    )
    print()


def test_es_comando_TEST():
    print("--- es_comando_TEST()")
    print(
        '["a"]: '
        + str(es_comando_TEST("a"))
        + "\n[0]: "
        + str(es_comando_TEST(0))
        + "\n[\\e]: "
        + str(es_comando_TEST("\\e"))
        + "\n[\\a]: "
        + str(es_comando_TEST("\\a"))
        + "\n[\\\\]: "
        + str(es_comando_TEST("\\\\"))
        + "\n[gen_palabra1]: "
        + str(es_comando_TEST(gen_palabra1))
    )
    print()


def test_anhadir_tabs_TEST():
    print("--- anhadir_tabs_TEST()")
    print(
        "1 tab:\n"
        + str(anhadir_tabs_TEST("codigo_test", 1))
        + "\n\n3 tabs:\n"
        + str(anhadir_tabs_TEST("codigo_test", 3))
    )
    print()


def test_digerir_comando_TEST():
    print("--- digerir_comando_TEST()")
    print()
    try:
        print("\\e: " + digerir_comando_TEST("\\e", 0))
    except Exception as e:
        print(f"Error capturado en \\e -{e}")

    try:
        print(f"\\eF: " + digerir_comando_TEST("\\eF", 0))
    except Exception as e:
        print(f"Error capturado en \\eF -{e}")

    try:
        print(f"\\n: " + digerir_comando_TEST("\\n", 0))
    except Exception as e:
        print(f"Error capturado en \\n -{e}")

    try:
        print(f"\\nF: " + digerir_comando_TEST("\\nF", 0))
    except Exception as e:
        print(f"Error capturado en \\nF -{e}")

    try:
        print(f"\\\\: " + digerir_comando_TEST("\\\\", 0))
    except Exception as e:
        print(f"Error capturado en \\\\ -{e}")

    try:
        print(f"\\\\F: " + digerir_comando_TEST("\\\\F", 0))
    except Exception as e:
        print(f"Error capturado en \\\\F -{e}")

    try:
        print(f"\\t: " + digerir_comando_TEST("\\t", 1))
    except Exception as e:
        print(f"Error capturado en \\t -{e}")

    try:
        print(f"\\tF: " + digerir_comando_TEST("\\tF", 0))
    except Exception as e:
        print(f"Error capturado en \\tF -{e}")

    try:
        print(f"\\x: " + digerir_comando_TEST("\\x", 0))
    except Exception as e:
        print(f"Error capturado en \\x -{e}")
    print()


def test_compilar_token_TEST():
    """
    posibles tokens:
    - array
    - string
    - nodo
    """
    print("--- digerir_comando_TEST()")
    print()
    print("- TEST ARRAY -")
    token = gen_letra2
    ite_adn = 0
    modo_eleccion = False
    adn = gen_letra2.get_adn()
    # print(f" {compilar_token_TEST(token, ite_adn, modo_eleccion, adn)}")
    print(f"get_adn(): {gen_char1.nombre,gen_char1.get_adn()}")
