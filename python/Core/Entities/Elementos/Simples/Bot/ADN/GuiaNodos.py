class Genoma:

    def __init__(self, adn: list):
        self.contexto = Genoma.Contexto()
        self.adn = adn

    def get_adn_lineal():
        pass

    def add_gen():
        pass

    class Contexto:

        def __init__(self):
            self.adn = Genoma.get_adn_lineal()
            self.ite = 0

        def next_adn(self):
            elemento = self.adn[self.ite]
            self.ite += 1
            return elemento


class Nodo:

    class Eleccion:

        def __init__(self, opciones: list):
            self.opciones = opciones

        def compilar(self, genoma: Genoma):
            contexto = genoma.contexto
            item = self.opciones[contexto.next_adn()]
            contexto.ite += 1

            if isinstance(item, str):
                return item

            if hasattr(
                item, "compilar"
            ):  # es Eleccion. Ej: Nodo.Eleccion([ _dato(), ... ,_variable()])
                return item.compilar(contexto)

            if callable(item):  # es una funcion. Ej: _dato()
                return item().compilar(contexto)

            if isinstance(
                item, list
            ):  # Array. Se puede encontrar como conjunto de elementos que conforman una posibilidad en una eleccion. Ej: [_a(), _b()]
                return self.compilar_lista(item, contexto)

            raise TypeError(f"Elemento no reconocido: {type(item)}")

    def compilar_lista(self, lista: list, genoma: Genoma):
        contexto = genoma.contexto
        resultado = ""
        partes = []

        for elemento in lista:

            if isinstance(elemento, str):
                partes.append(elemento)
                continue

            if hasattr(elemento, "compilar"):
                partes.append(elemento.compilar(contexto))
                continue

            if callable(elemento):
                partes.append(elemento().compilar(contexto))
                continue

            if isinstance(elemento, list):
                partes.append(self.compilar_lista(elemento, contexto))
                continue

        return resultado.join(partes)

    def __init__(self, nombre: str, items: list, genoma: Genoma):
        contexto = genoma.contexto
        self.nombre = nombre
        self.items = items
        self.contexto = contexto

    def get_nombre(self):
        return self.nombre

    def compilar(self, genoma: Genoma):
        return self.compilar_lista(self.items, genoma)


###################################################################################
#
#
#   #   Inicio definicion de gramatica  #
#
#
####################################################################################


def _programa():
    return Nodo(
        "_programa",
        [
            _codigoInyectado(),  # -----------------------    Codigo inyectado post analisis
            "\\n",
            "\\n",
            "#---------------------------------",
            "\\n",
            "# FIN IMPORTS LIBRERIAS POST ANALISIS",
            "\\n",
            _importsHardCoded(),  # ----------------------    imports que todos los bots disponen sin coste
            "\\n",
            "#---------------------------------",
            "\\n",
            "#---------------------------------",
            "\\n",
            "\\n",
            "\\n",
            "#---------------------------------",
            "\\n",
            "# Clases:",
            "\\n",
            "#---------------------------------",
            "\\n",
            _clases(),
            "\\n",
            "#---------------------------------",
            "\\n",
            "\\n",
            "\\n",
            "#---------------------------------",
            "\\n",
            "# Funciones:",
            "\\n",
            "#---------------------------------",
            "\\n",
            _funciones(),
            # "\\n",
            # "#---------------------------------",
            # "\\n",
            # "# Variables globales:",
            # "\\n",
            # "#---------------------------------",
            # "\\n",
            # _declaracionVariablesGlobales(),
            "\\n",
            "\\n",
            "\\n",
            "#---------------------------------",
            "\\n",
            "# Codigo:",
            "\\n",
            "#---------------------------------",
            "\\n",
            _codigo(),
        ],
    )


def _importsHardCoded():
    return Nodo("_importsBasicos", ["from functools import reduce"])


def _asignacion():
    return Nodo(
        "_asignacion",
        [
            _variable(),
            " = ",
            Nodo.Eleccion([_dato(), _variable(), _llamadaFuncion(), _operacion()]),
            "\\n",
        ],
    )


def _control():
    return Nodo(
        "_control",
        [
            Nodo.Eleccion(
                [
                    _bucle(),
                    _condicional(),
                    _controlFunciones(),
                    _controlEstructural(),
                    _declaracionEstructural(),
                ]
            )
        ],
    )


def _bucle():
    return Nodo("_bucle", [Nodo.Eleccion([_for(), _while(), _break(), _continue()])])


def _for():
    return Nodo(
        "_for", [Nodo.Eleccion([_forLista(), _forIndice(), _forNumerico(), _forDict()])]
    )


def _condicional():
    return Nodo("_condicional", [Nodo.Eleccion([_if(), _match()])])


def _if():
    return Nodo(
        "_if",
        [
            "if ",
            _condicion(),
            ":",
            "\\n",
            "\\t",
            _codigo(),
            "\\n",
            Nodo.Eleccion([[Nodo.Eleccion([_else(), _elif()])], _stop()]),
        ],
    )


def _elif():
    return Nodo(
        "_elif",
        [
            "elif ",
            _condicion(),
            ":",
            "\\n",
            "\\t",
            _codigo(),
            "\\n",
            Nodo.Eleccion([Nodo.Eleccion([_else(), _elif()]), _stop()]),
            "\\n",
        ],
    )


def _else():
    return Nodo("_else", ["else:", "\\n", "\\t", _codigo(), "\\n"])


def _condicion():
    return Nodo("_condicion", ["(", _dato(), " ", _comparacion(), " ", _dato(), ")"])


def _controlFunciones():
    return Nodo("_controlFunciones", [Nodo.Eleccion([_return(), _yield()])])


def _return():
    return Nodo(
        "_return",
        [
            "return ",
            Nodo.Eleccion([["\\e", [_dato(), _llamadaFuncion()]], _stop()]),
            "\\n",
        ],
    )


def _yield():
    return Nodo(
        "_yield", ["yield ", " ", Nodo.Eleccion([_dato(), _llamadaFuncion()]), "\\n"]
    )


def _controlEstructural():
    return Nodo("_controlEstructural", [_try()])


def _try():
    return Nodo(
        "_try",
        [
            "try:",
            "\\n",
            "\\t",
            _codigo(),
            "\\n",
            "except",
            Nodo.Eleccion([[" ", _palabra()], _stop()]),
            ":",
            "\\n",
            "\\t",
            _codigo(),
            "\\n",
            Nodo.Eleccion([_else(), _finally(), [_else(), _finally()]]),
        ],
    )


def _finally():
    return Nodo("_finally", ["finally:", "\\n", "\\t", _codigo(), "\\n"])


def _with():
    return Nodo(
        "_with",
        [
            "with open(",
            _textoDirectorioLocal(),
            Nodo.Eleccion(["r", "w"]),
            ") as ",
            _variable(),
            ":",
            "\\n",
            _codigo(),
        ],
    )


def _declaracionEstructural():
    return Nodo(
        "_declaracionEstructural", [Nodo.Eleccion([_llamadaFuncion(), _clase()])]
    )


def _argumentos():
    return Nodo(
        "_argumentos", [[_argumento(), Nodo.Eleccion([[", ", _argumentos()], _stop()])]]
    )


def _argumento():
    return Nodo("_argumento", [_dato()])


def _variablesClase():
    return Nodo([_variable(), Nodo.Eleccion([_variablesClase(), _stop()])])


def _funcionesClase():
    return Nodo([_funcion(), Nodo.Eleccion([_funciones(), _stop()])])


def _operacion():
    return Nodo(
        [
            Nodo.Eleccion(
                [_operacionAritmetica(), _operacionLogica(), _operacionBitwise()]
            )
        ]
    )


def _operacionAritmetica():
    return Nodo(
        [
            Nodo.Eleccion(
                [
                    _suma(),
                    _resta(),
                    _multiplicacion(),
                    _division(),
                    _modulo(),
                    _potencia(),
                    _raiz(),
                ]
            )
        ]
    )


def _suma():
    return Nodo(
        [
            Nodo.Eleccion([_variable(), __numero()(), _funcion(), _operacion()]),
            " ",
            _simboloSuma(),
            " ",
            Nodo.Eleccion([_variable(), __numero()(), _funcion(), _operacion()]),
        ]
    )


def _resta():
    return Nodo(
        [
            Nodo.Eleccion([_variable(), __numero()(), _funcion(), _operacion()]),
            " ",
            _simboloResta(),
            " ",
            Nodo.Eleccion([_variable(), __numero()(), _funcion(), _operacion()]),
        ]
    )


def _multiplicacion():
    return Nodo(
        [
            Nodo.Eleccion([_variable(), __numero(), _funcion(), _operacion()]),
            " ",
            _simboloMultiplicacion(),
            " ",
            Nodo.Eleccion([_variable(), __numero(), _funcion(), _operacion()]),
        ]
    )


def _division():
    return Nodo(
        [
            Nodo.Eleccion([_variable(), _numero(), _funcion(), _operacion()]),
            " ",
            _simboloDivision(),
            " ",
            Nodo.Eleccion([_variable(), _numero(), _funcion(), _operacion()]),
        ]
    )


def _modulo():
    return Nodo(
        [
            Nodo.Eleccion([_variable(), _numero(), _funcion(), _operacion()]),
            " ",
            _simboloModulo(),
            " ",
            Nodo.Eleccion([_variable(), _numero(), _funcion(), _operacion()]),
        ]
    )


def _potencia():
    return Nodo(
        [
            Nodo.Eleccion([_variable(), _numero(), _funcion(), _operacion()]),
            " ",
            _simboloPotencia(),
            " ",
            Nodo.Eleccion([_variable(), _numero(), _funcion(), _operacion()]),
        ]
    )


def _raiz():
    return Nodo(
        [
            Nodo.Eleccion([_variable(), _numero()(), _funcion(), _operacion()]),
            " ** (1 / ",
            Nodo.Eleccion([_variable(), _numero()(), _funcion(), _operacion()]),
            ")",
        ]
    )


def _comparacion():
    return Nodo(
        "_comparacion", ["(", _dato(), " ", _simboloComparacion(), " ", _dato(), ")"]
    )


def _simboloSuma():
    return Nodo("_simboloSuma", ["+"])


def _simboloResta():
    return Nodo("_simboloResta", ["-"])


def _simboloMultiplicacion():
    return Nodo("_simboloMultiplicacion", ["*"])


def _simboloDivision():
    return Nodo("_simboloDivision", ["/"])


def _simboloModulo():
    return Nodo("_simboloModulo", ["%"])


def _simboloPotencia():
    return Nodo("_simboloPotencia", ["**"])


def _true():
    return Nodo("_true", ["True"])


def _false():
    return Nodo("_false", ["False"])


def _operacionBitwise():
    return Nodo(
        "_operacionBitwise",
        [
            Nodo.Eleccion(
                [
                    _mascaraAnd(),
                    _mascaraOr(),
                    _mascaraNot(),
                    _mascaraShiftIzquierda(),
                    _mascaraShiftDerecha(),
                ]
            )
        ],
    )


def _mascaraAnd():
    return Nodo("_mascaraAnd", [_dato(), " & ", _dato()])


def _mascaraOr():
    return Nodo("_mascaraOr", [_dato(), "|", _dato()])


def _mascaraNot():
    return Nodo("_mascaraNot", ["~", _dato()])


def _comentario():
    return Nodo(
        "_comentario", [Nodo.Eleccion([_comentarioLinea(), _comentarioBloque()])]
    )


def _comentarioLinea():
    return Nodo("_comentarioLinea", ["# ", _contenidoComentario(), "\\n"])


def _comentarioBloque():
    return Nodo(
        "_comentarioBloque", ["'''", "\\n", _contenidoComentario(), "\\n", "'''"]
    )


def _contenidoComentario():
    return Nodo(
        "_contenidoComentario",
        [
            Nodo.Eleccion([_poolStrings(), _textoLetras()]),
            Nodo.Eleccion([_contenidoComentario(), _stop()]),
        ],
    )


def _textoLetrasSimbolos():
    return Nodo(
        "_textoLetrasSimbolos",
        [
            Nodo.Eleccion([_letra(), _simbolo()]),
            Nodo.Eleccion([_textoLetrasSimbolos(), _stop()]),
        ],
    )


def _textoLetrasNumeros():
    return Nodo(
        "_textoLetrasNumeros",
        [
            Nodo.Eleccion([_letra(), _digito()]),
            Nodo.Eleccion([_textoLetrasNumeros(), _stop()]),
        ],
    )


def _textoLetras():
    return Nodo("_textoLetras", [_letra(), Nodo.Eleccion([_textoLetras(), _stop()])])


def _textos():
    return Nodo(
        "_textos",
        [
            Nodo.Eleccion(
                [
                    _textoLetras(),
                    _textoLetrasNumeros(),
                    _textoLetrasSimbolos(),
                    _textoDirectorios(),
                ]
            )
        ],
    )


def _variable():
    return Nodo("_variable", [_letra(), _textoLetrasNumeros()])


def _funciones():
    return Nodo(
        "_funciones", [_funcion(), "\\n", Nodo.Eleccion([_funciones(), _stop()]), "\\n"]
    )


# def _declaracionVariablesGlobales():
#     return Nodo(
#         "_declaracionVariablesGlobales",
#         [
#             _variable(),
#             "\\n",
#             Nodo.Eleccion([_declaracionVariablesGlobales(), _stop()]),
#             "\\n",
#         ],
#     )


def _codigo():
    return Nodo(
        "_codigo",
        [
            Nodo.Eleccion(
                [
                    _operacion(),
                    _asignacion(),
                    _control(),
                    _funcion(),
                    _clase(),
                    _comentario(),
                ]
            ),
            Nodo.Eleccion([_codigo(), _stop()]),
        ],
    )


def _conjunto():
    return Nodo(
        "_conjunto", [Nodo.Eleccion([_lista(), _tupla(), _diccionario(), _set()])]
    )


def _set():
    return Nodo("_set", [_variable(), " = ", "{", _argumentos(), "}"])


def _diccionario():
    return Nodo("_diccionario", [_variable(), " = ", "{", _argumentosKV(), "}", "\n"])


def _argumentosKV():
    return Nodo(
        "_argumentosKV",
        [_argumentoKV(), Nodo.Eleccion([[", ", _argumentosKV()], _stop()])],
    )


def _argumentoKV():
    return Nodo("_argumentoKV", [_string(), ": ", Nodo.Eleccion([_dato(), _funcion()])])


def _tupla():
    return Nodo("_tupla", ["(", _argumentos(), ")", "\\n"])


def _lista():
    return Nodo("_lista", ["[", _argumentos(), "]", "\\n"])


def _bool():
    return Nodo("_bool", [Nodo.Eleccion([_true(), _false()])])


def _string():
    return Nodo("_string", ['"', _palabra(), '"'])


def _palabra():
    return Nodo("_palabra", [_char(), Nodo.Eleccion([_palabra(), _stop()])])


def _char():
    return Nodo("_char", [Nodo.Eleccion([_letra(), _simbolo()])])


def _letra():
    return Nodo(
        "_letra",
        [
            Nodo.Eleccion(
                [
                    "a",
                    "b",
                    "c",
                    "d",
                    "e",
                    "f",
                    "g",
                    "h",
                    "i",
                    "j",
                    "k",
                    "l",
                    "m",
                    "n",
                    "ñ",
                    "o",
                    "p",
                    "q",
                    "r",
                    "s",
                    "t",
                    "u",
                    "v",
                    "w",
                    "x",
                    "y",
                    "z",
                    "A",
                    "B",
                    "C",
                    "D",
                    "E",
                    "F",
                    "G",
                    "H",
                    "I",
                    "J",
                    "K",
                    "L",
                    "M",
                    "N",
                    "Ñ",
                    "O",
                    "P",
                    "Q",
                    "R",
                    "S",
                    "T",
                    "U",
                    "V",
                    "W",
                    "X",
                    "Y",
                    "Z",
                ]
            )
        ],
    )


def _simbolo():
    return Nodo(
        "_simbolo",
        [
            Nodo.Eleccion(
                [
                    _simboloAritmetico(),
                    _simboloLogico(),
                    _simboloComparacion(),
                    _parentesis(),
                    _corchetes(),
                    _llaves(),
                    _comillas(),
                    _simboloTexto(),
                ]
            )
        ],
    )


def _simboloAritmetico():
    return Nodo(
        "_simboloAritmetico",
        [
            Nodo.Eleccion(
                [
                    _simboloSuma(),
                    _simboloResta(),
                    _simboloMultiplicacion(),
                    _simboloDivision(),
                    _simboloModulo(),
                    _simboloPotencia(),
                ]
            )
        ],
    )


def _simboloLogico():
    return Nodo("_simboloLogico", [Nodo.Eleccion([_and(), _or(), _not()])])


def _and():
    return Nodo("_and", ["and"])


def _or():
    return Nodo("_or", ["or"])


def _not():
    return Nodo("_not", ["not"])


def _simboloComparacion():
    return Nodo(
        "",
        [
            Nodo.Eleccion(
                [
                    _equal(),
                    _notEqual(),
                    _greaterThan(),
                    _lowerThan(),
                    _greaterOrEqualThan(),
                    _lowerOrEqualThan(),
                ]
            )
        ],
    )


def _equal():
    return Nodo("_equal", ["=="])


def _notEqual():
    return Nodo("_notEqual", ["!="])


def _greaterThan():
    return Nodo("_greaterThan", [">"])


def _lowerThan():
    return Nodo("_lowerThan", ["<"])


def _greaterOrEqualThan():
    return Nodo("_greaterOrEqualThan", [">="])


def _lowerOrEqualThan():
    return Nodo("_lowerOrEqualThan", ["<="])


def _simboloTexto():
    return Nodo(
        "_simboloTexto",
        [
            " ",
            "!",
            '"',
            "@",
            "·",
            "#",
            "$",
            "~",
            "%",
            "&",
            "¬",
            "/",
            "?",
            "¿",
            "¡",
            "^",
            "`",
            "+",
            "*",
            "¨",
            "ç",
            ",",
            ";",
            ".",
            ":",
            "-",
            "_",
            "\n",
            "\t",
            "\\",
            "<",
            ">",
            "º",
            "ª",
        ],
    )


def _parentesis():
    return Nodo("_parentesis", [Nodo.Eleccion(["(", ")"])])


def _corchetes():
    return Nodo("_corchetes", [Nodo.Eleccion(["[", "]"])])


def _llaves():
    return Nodo("_llaves", [Nodo.Eleccion(["{", "}"])])


def _comillas():
    return Nodo("_comillas", ['"'])


def _numero():
    return Nodo(
        "__numero",
        [
            Nodo.Eleccion([_positivo(), _negativo()]),
            Nodo.Eleccion([_integer(), _double(), _complex()]),
        ],
    )


def _integer():
    return Nodo("_integer", [_digito(), Nodo.Eleccion([_integer(), _stop()])])


def _double():
    return Nodo("_double", [_integer(), ".", _integer()])


def _complex():
    return Nodo(
        "_complex",
        [
            "complex(",
            Nodo.Eleccion([_positivo(), _negativo()]),
            Nodo.Eleccion([_integer(), _double()]),
            ", ",
            Nodo.Eleccion([_positivo(), _negativo()]),
            Nodo.Eleccion([_integer(), _double()]),
            ")",
        ],
    )


def _positivo():
    return Nodo("_positivo", [""])


def _negativo():
    return Nodo("_negativo", ["-"])


def _digito():
    return Nodo(
        "_digito", [Nodo.Eleccion(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])]
    )


def _dato():
    return Nodo(
        "_dato",
        [
            Nodo.Eleccion(
                [
                    _numero(),
                    _string(),
                    _bool(),
                    _conjunto(),
                    _variable(),
                    _funcion(),
                    _leerAtributoClase(),
                    _llamadaFuncion(),
                    _invocarMetodo(),
                ]
            )
        ],
    )


def _operacionLogica():
    return Nodo(
        "_operacionLogica",
        [
            Nodo.Eleccion(
                [
                    _operacionAnd(),
                    _operacionOr(),
                    _operacionNot(),
                    _comparacion(),
                    _true(),
                    _false(),
                ]
            )
        ],
    )


def _operacionAnd():
    return Nodo(
        "_operacionAnd", ["(", _comparacion(), " ", _and(), " ", _comparacion(), ")"]
    )


def _operacionOr():
    return Nodo(
        "_operacionOr", ["(", _comparacion(), " ", _or(), " ", _comparacion(), ")"]
    )


def _operacionNot():
    return Nodo("_operacionNot", [_not(), "(", _comparacion(), ")"])


def _mascaraShiftIzquierda():
    return Nodo("_mascaraShiftIzquierda", ["<<", _dato()])


def _mascaraShiftDerecha():
    return Nodo("_mascaraShiftDerecha", [">>", _dato()])


def _forLista():
    return Nodo(
        "_forLista",
        [
            "for ",
            _variable(),
            " in ",
            _variable(),
            ":",
            "\\n",
            "\\t",
            _codigoFuncion(),
            "\\n",
        ],
    )


def _forIndice():
    return Nodo(
        "_forIndice",
        [
            "for ",
            _variable(),
            ", ",
            _variable(),
            " in enumerate(",
            _variable(),
            ", start=",
            _integer(),
            "):",
            "\\n",
            "\\t",
            _codigoFuncion(),
            "\\n",
        ],
    )


def _forNumerico():
    return Nodo(
        "_forNumerico",
        [
            "for ",
            _variable(),
            " in range(",
            Nodo.Eleccion(
                [
                    [Nodo.Eleccion([_integer(), _variable(), _llamadaFuncion()])],
                    [
                        Nodo.Eleccion([_integer(), _variable(), _llamadaFuncion()]),
                        ", ",
                        Nodo.Eleccion([_integer(), _variable(), _llamadaFuncion()]),
                    ],
                    [
                        Nodo.Eleccion([_integer(), _variable(), _llamadaFuncion()]),
                        ", ",
                        Nodo.Eleccion([_integer(), _variable(), _llamadaFuncion()]),
                        ", ",
                        Nodo.Eleccion([_integer(), _variable(), _llamadaFuncion()]),
                    ],
                ]
            ),
            "):",
            "\\n",
            "\\t",
            _codigoBucle(),
            "\\n",
            Nodo.Eleccion([_forElse(), _stop()]),
        ],
    )


def _forDict():
    return Nodo(
        "_forDict",
        [
            "for ",
            _variable(),
            " in ",
            _variable(),
            ":",
            "\\n",
            "\\t",
            _codigoFuncion(),
            "\\n",
        ],
    )


def _break():
    return Nodo("_break", ["break ", "\\n"])


def _while():
    return Nodo(
        "_while",
        [
            "while ",
            _condicion(),
            ":",
            "\\n",
            "\\t",
            _codigo(),
            "\\n",
            Nodo.Eleccion([["\\n", _else()], _stop()]),
            "\\n",
        ],
    )


def _continue():
    return Nodo("_continue", ["continue", "\\n"])


def _match():
    return Nodo(
        "_match",
        [
            "match ",
            Nodo.Eleccion([_variable(), _funcion()]),
            ":",
            "\\n",
            _cases(),
            Nodo.Eleccion([["case _:", "\\n", _codigo()], _stop()]),
        ],
    )


def _cases():
    return Nodo(
        "_cases",
        [
            "case ",
            _palabra(),
            ":",
            "\n",
            "\\t",
            _codigo(),
            "\\n",
            Nodo.Eleccion([_cases(), _stop()]),
        ],
    )


def _declaracionFuncion():
    return Nodo(
        "_declaracionFuncion",
        [
            Nodo.Eleccion(
                [
                    _declaracionFuncionNormal(),
                    _declaracionFuncionMetodo(),
                ]
            ),
            "\\n",
        ],
    )


def _declaracionFuncionNormal():
    return Nodo(
        "_declaracionFuncionNormal",
        [
            "def ",
            _letra(),
            _textoLetrasNumeros(),
            "(",
            _argumentos(),
            "):",
            "\\n",
            "\\t",
            Nodo.Eleccion([[_pass()], [_codigoFuncion()]]),
            "\\n",
        ],
    )


def _declaracionFuncionAsincrona():
    return Nodo(
        "_declaracionFuncionAsincrona",
        [
            "async def ",
            _letra(),
            _textoLetrasNumeros(),
            "(",
            _argumentos(),
            ")=",
            "\\n",
            "\\t",
            Nodo.Eleccion([[_pass()], [_codigoFuncionAsincrona()]]),
            "\\n",
        ],
    )


def _declaracionFuncionGeneradora():
    return Nodo(
        "_declaracionFuncionGeneradora",
        [
            "def ",
            _letra(),
            _textoLetrasNumeros(),
            "(",
            _argumentos(),
            ")=",
            "\\n",
            "\\t",
            _codigoGenerador(),
            "\\n",
        ],
    )


def _declaracionFuncionLambda():
    return Nodo(
        "_declaracionFuncionLambda",
        [
            "lambda ",
            _argumentosLambda(),
            "= ",
            _expresionSimple(),
        ],
    )


def _declaracionMetodo():
    return Nodo(
        "_declaracionMetodo",
        [
            Nodo.Eleccion(
                [
                    _declaracionMetodoNormal(),
                    _declaracionMetodoAsincrono(),
                    _declaracionMetodoEstatico(),
                    _declaracionMetodoClase(),
                ]
            ),
            Nodo.Eleccion([_declaracionMetodo(), _stop()]),
        ],
    )


def _declaracionMetodoNormal():
    return Nodo(
        "_declaracionMetodoNormal",
        [
            "def ",
            _letra(),
            _textoLetrasNumeros(),
            "(self",
            Nodo.Eleccion([[", ", _argumentos()], _stop()]),
            ")=",
            "\\n",
            "\\t",
            Nodo.Eleccion([_pass(), _codigoFuncion()]),
            "\\n",
        ],
    )


def _declaracionMetodoAsincrono():
    return Nodo(
        "_declaracionMetodoAsincrono",
        [
            "async def ",
            _letra(),
            _textoLetrasNumeros(),
            "(self",
            Nodo.Eleccion([[", ", _argumentos()], _stop()]),
            ")=",
            "\\n",
            "\\t",
            Nodo.Eleccion([_pass(), _codigoFuncionAsincrona()]),
            "\\n",
        ],
    )


def _declaracionMetodoEstatico():
    return Nodo(
        "_declaracionMetodoEstatico",
        [
            "@staticmethod",
            "\\n",
            "def ",
            _letra(),
            _textoLetrasNumeros(),
            "(",
            _argumentos(),
            ")=",
            "\\n",
            "\\t",
            Nodo.Eleccion([_pass(), _codigoFuncion()]),
            "\\n",
        ],
    )


def _declaracionMetodoClase():
    return Nodo(
        "_declaracionMetodoClase",
        [
            "@classmethod",
            "\\n",
            "def ",
            _letra(),
            _textoLetrasNumeros(),
            "(cls",
            Nodo.Eleccion([[", ", _argumentos()], _stop()]),
            ")=",
            "\\n",
            "\\t",
            Nodo.Eleccion([_pass(), _codigoFuncion()]),
            "\\n",
        ],
    )


def _clase():
    return Nodo(
        "_clase",
        [Nodo.Eleccion([_declaracionClase(), _instanciacionClase(), _usarClase()])],
    )


def _herencia():
    return Nodo(
        "_herencia",
        [
            _letra(),
            _textoLetrasNumeros(),
            Nodo.Eleccion([[", ", _herencia()], _stop()]),
        ],
    )


def _metodosClase():
    return Nodo(
        "_metodosClase",
        [
            Nodo.Eleccion(
                [[_declaracionMetodo(), "\\n", "\\t", _metodosClase()], _stop()]
            )
        ],
    )


def _constructorClase():
    return Nodo(
        "_constructorClase",
        [
            "def __init__(self",
            Nodo.Eleccion([[", ", _argumentos()], _stop()]),
            ")=",
            "\\n",
            "\\t",
            Nodo.Eleccion([_pass(), _codigoFuncion()]),
            "\\n",
        ],
    )


def _pass():
    return Nodo("_pass", ["pass"])


def _atributosClase():
    return Nodo(
        "_atributosClase",
        [
            Nodo.Eleccion(
                [[_variable(), " = ", _dato(), "\\n", _atributosClase()], _stop()]
            )
        ],
    )


def _builtinOtrosUtilidad():
    return Nodo(
        "_builtinOtrosUtilidad",
        [
            Nodo.Eleccion(
                [
                    ["len(", _argumentos(), ")"],
                    ["all(", _argumentos(), ")"],
                    ["any(", _argumentos(), ")"],
                    ["zip(", _argumentos(), ")"],
                    ["slice(", _argumentos(), ")"],
                    ["super(", _argumentos(), ")"],
                    ["object(", _argumentos(), ")"],
                    ["staticmethod(", _argumentos(), ")"],
                    ["classmethod(", _argumentos(), ")"],
                    ["property(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinOtrosEjecucion():
    return Nodo(
        "_builtinOtrosEjecucion",
        [
            Nodo.Eleccion(
                [
                    ["eval(", _argumentos(), ")"],
                    ["exec(", _argumentos(), ")"],
                    ["compile(", _argumentos(), ")"],
                    ["__import__(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinOtros():
    return Nodo(
        "_builtinOtros",
        [Nodo.Eleccion([_builtinOtrosUtilidad(), _builtinOtrosEjecucion()])],
    )


def _builtinIOFichero():
    return Nodo(
        "_builtinIOFichero",
        [
            Nodo.Eleccion(
                [
                    ["open(", _argumentos(), ")"],
                    ["read(", _argumentos(), ")"],
                    ["write(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinIOTexto():
    return Nodo(
        "_builtinIOTexto",
        [
            Nodo.Eleccion(
                [
                    ["print(", _argumentos(), ")"],
                    ["input(", _argumentos(), ")"],
                    ["format(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinIO():
    return Nodo("_builtinIO", [Nodo.Eleccion([_builtinIOTexto(), _builtinIOFichero()])])


def _builtinInspeccionAtributos():
    return Nodo(
        "_builtinInspeccionAtributos",
        [
            Nodo.Eleccion(
                [
                    ["hasattr(", _argumentos(), ")"],
                    ["getattr(", _argumentos(), ")"],
                    ["setattr(", _argumentos(), ")"],
                    ["delattr(", _argumentos(), ")"],
                    ["dir(", _argumentos(), ")"],
                    ["vars(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinInspeccionTipos():
    return Nodo(
        "_builtinInspeccionTipos",
        [
            Nodo.Eleccion(
                [
                    ["type(", _argumentos(), ")"],
                    ["isinstance(", _argumentos(), ")"],
                    ["issubclass(", _argumentos(), ")"],
                    ["callable(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinInspeccion():
    return Nodo(
        "_builtinInspeccion",
        [Nodo.Eleccion([_builtinInspeccionTipos(), _builtinInspeccionAtributos()])],
    )


def _builtinIteracionFuncional():
    return Nodo(
        "_builtinIteracionFuncional",
        [
            Nodo.Eleccion(
                [
                    ["map(", _argumentos(), ")"],
                    ["filter(", _argumentos(), ")"],
                    ["reduce(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinIteracionBasica():
    return Nodo(
        "_builtinIteracionBasica",
        [
            Nodo.Eleccion(
                [
                    ["range(", _argumentos(), ")"],
                    ["enumerate(", _argumentos(), ")"],
                    ["zip(", _argumentos(), ")"],
                    ["reversed(", _argumentos(), ")"],
                    ["sorted(", _argumentos(), ")"],
                    ["iter(", _argumentos(), ")"],
                    ["next(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinIteracion():
    return Nodo(
        "_builtinIteracion",
        [Nodo.Eleccion([_builtinIteracionBasica(), _builtinIteracionFuncional()])],
    )


def _builtinMatematicasAvanzadas():
    return Nodo(
        "_builtinMatematicasAvanzadas",
        [Nodo.Eleccion([["hash(", _argumentos(), ")"], ["id(", _argumentos(), ")"]])],
    )


def _builtinMatematicasBasicas():
    return Nodo(
        "",
        [
            Nodo.Eleccion(
                [
                    ["abs(", _argumentos(), ")"],
                    ["round(", _argumentos(), ")"],
                    ["min(", _argumentos(), ")"],
                    ["max(", _argumentos(), ")"],
                    ["sum(", _argumentos(), ")"],
                    ["pow(", _argumentos(), ")"],
                    ["divmod(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinMatematicas():
    return Nodo(
        "_builtinMatematicas",
        [Nodo.Eleccion([_builtinMatematicasBasicas(), _builtinMatematicasAvanzadas()])],
    )


def _builtinConversionTexto():
    return Nodo(
        "_builtinConversionTexto",
        [
            Nodo.Eleccion(
                [
                    ["str(", _argumentos(), ")"],
                    ["repr(", _argumentos(), ")"],
                    ["ascii(", _argumentos(), ")"],
                    ["chr(", _argumentos(), ")"],
                    ["ord(", _argumentos(), ")"],
                    ["hex(", _argumentos(), ")"],
                    ["oct(", _argumentos(), ")"],
                    ["bin(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinConversionSecuencia():
    return Nodo(
        "_builtinConversionSecuencia",
        [
            Nodo.Eleccion(
                [
                    ["list(", _argumentos(), ")"],
                    ["tuple(", _argumentos(), ")"],
                    ["set(", _argumentos(), ")"],
                    ["frozenset(", _argumentos(), ")"],
                    ["dict(", _argumentos(), ")"],
                    ["bytes(", _argumentos(), ")"],
                    ["bytearray(", _argumentos(), ")"],
                ]
            )
        ],
    )


def _builtinConversionNumerico():
    return Nodo(
        "_builtinConversionNumerico",
        [
            Nodo.Eleccion()[
                ["int(", _argumentos(), ")"],
                ["float(", _argumentos(), ")"],
                ["complex(", _argumentos(), ")"],
                ["bool(", _argumentos(), ")"],
            ],
        ],
    )


def _builtinConversion():
    return Nodo(
        "_builtinConversion",
        [
            Nodo.Eleccion(
                [
                    _builtinConversionNumerico(),
                    _builtinConversionSecuencia(),
                    _builtinConversionTexto(),
                ]
            )
        ],
    )


def _builtinTipos():
    return Nodo(
        "_builtinTipos",
        [
            Nodo.Eleccion(
                [
                    "int",
                    "float",
                    "str",
                    "bool",
                    "list",
                    "dict",
                    "tuple",
                    "set",
                    "complex",
                    "bytes",
                    "bytearray",
                    "frozenset",
                ]
            )
        ],
    )


def _builtin():
    return Nodo(
        "_builtin",
        [
            Nodo.Eleccion(
                [
                    _builtinTipos(),
                    _builtinConversion(),
                    _builtinMatematicas(),
                    _builtinIteracion(),
                    _builtinInspeccion(),
                    _builtinIO(),
                    _builtinOtros(),
                ]
            )
        ],
    )


def _declaracionClase():
    return Nodo(
        "_declaracionClase",
        [
            "class ",
            _letra(),
            _textoLetrasNumeros(),
            Nodo.Eleccion([["(", _herencia(), ")"], _stop()]),
            ":",
            "\\n",
            "\\t",
            _atributosClase(),
            "\\n",
            "\\t",
            _constructor(),
            "\\n",
            "\\t",
            _metodosClase(),
            "\\n",
        ],
    )


# TODO _constructor
def _constructor():
    return Nodo("_constructor", [])


def _instanciacionClase():
    return Nodo(
        "_instanciacionClase",
        [
            _variable(),
            " = ",
            _letra(),
            _textoLetrasNumeros(),
            "(",
            Nodo.Eleccion([[_argumentos()], _stop()]),
            ")",
        ],
    )


def _usoClase():
    return Nodo("_usoClase", [Nodo.Eleccion([_invocarMetodo(), _atributoClase()])])


def _encadenarMetodo():
    return Nodo(
        "_encadenarMetodo",
        [
            _variable(),
            "(",
            Nodo.Eleccion([_argumentos(), _stop()]),
            ")",
            Nodo.Eleccion([[".", _encadenarMetodo()], _stop()]),
        ],
    )


def _atributoClase():
    return Nodo(
        "_atributoClase",
        [Nodo.Eleccion([_leerAtributoClase(), _escribirAtributoClase()])],
    )


def _leerAtributoClase():
    return Nodo("_leerAtributoClase", ["variable", ".", "variable"])


def _escribirAtributoClase():
    return Nodo("", [_variable(), ".", _variable(), " = ", _dato()])


def _raise():
    return Nodo(
        "_raise",
        [
            "raise",
            Nodo.Eleccion(
                [[" ", Nodo.Eleccion([_llamadaFuncion(), _variable()])], _stop()]
            ),
        ],
    )


def _ejecucion():
    return Nodo(
        "_ejecucion",
        [
            Nodo.Eleccion(
                [_funcion(), _clase(), _builtin(), _acessoFichero(), _accesoInternet()]
            )
        ],
    )


def _funcion():
    return Nodo("_funcion", [Nodo.Eleccion(["declaracionFuncion", "llamadaFuncion"])])


def _llamadaFuncion():
    return Nodo(
        "_llamadaFuncion",
        [_variable(), "(", Nodo.Eleccion([[_argumentos()], _stop()]), ")"],
    )


def _invocarMetodo():
    return Nodo(
        "_invocarMetodo",
        [Nodo.Eleccion([_variable(), _llamadaFuncion()]), ".", _encadenarMetodo()],
    )


def _accesoRecurso():
    return Nodo("_accesoRecurso", [_accesoFichero(), _accesoInternet()])


def _accesoFichero():
    return Nodo(
        "_accesoFichero",
        [
            Nodo.Eleccion(
                [
                    _leerFichero(),
                    _escribirFichero(),
                    _anadirFichero(),
                    _leerEscribirFichero(),
                ]
            )
        ],
    )


def _leerFichero():
    return Nodo(
        "_leerFichero",
        [
            "with open(",
            _textoDirectorioLocal(),
            ", 'r') as ",
            _variable(),
            "=",
            "\\n",
            "\\t",
            _codigoFuncion(),
        ],
    )


def _escribirFichero():
    return Nodo(
        "_escribirFichero",
        [
            "with open(",
            _textoDirectorioLocal(),
            ", 'w') as ",
            _variable(),
            "=",
            "\\n",
            "\\t",
            _codigoFuncion(),
        ],
    )


def _anadirFichero():
    return Nodo(
        "_anadirFichero",
        [
            "with open(",
            _textoDirectorioLocal(),
            ", 'a') as ",
            _variable(),
            "=",
            "\\n",
            "\\t",
            _codigoFuncion(),
        ],
    )


def _leerEscribirFichero():
    return Nodo(
        "_leerEscribirFichero",
        [
            "with open(",
            _textoDirectorioLocal(),
            ", 'r+') as ",
            _variable(),
            "=",
            "\\n",
            "\\t",
            _codigoFuncion(),
        ],
    )


def _accesoInternet():
    return Nodo("_accesoInternet", [Nodo.Eleccion([_httpGet(), _httpPost()])])


def _httpGet():
    return Nodo("_httpGet", ["requests.get(", _textoDirectorioWeb(), ")"])


def _httpPost():
    return Nodo(
        "_httpPost", ["requests.post(", _textoDirectorioWeb(), ", data=", _dato(), ")"]
    )


def _textoDirectorios():
    return Nodo(
        "_textoDirectorios",
        [Nodo.Eleccion([_textoDirectorioLocal(), _textoDirectorioWeb()])],
    )


def _textoDirectorioLocal():
    return Nodo(
        "_textoDirectorioLocal",
        [
            Nodo.Eleccion(
                [
                    _textoDirectorioWindows(),
                    _textoDirectorioLinux(),
                    _textoDirectorioMac(),
                ]
            )
        ],
    )


def _textoDirectorioWindows():
    return Nodo(
        "_textoDirectorioWindows",
        [
            Nodo.Eleccion([_letra(), _digito(), _simboloDirectorioWindows()]),
            Nodo.Eleccion([["\\\\", _textoDirectorioWindows()], _stop()]),
        ],
    )


def _textoDirectorioLinux():
    return Nodo(
        "_textoDirectorioLinux",
        [
            Nodo.Eleccion(["letra", _digito(), _simboloDirectorioLinux()]),
            Nodo.Eleccion([["/", _textoDirectorioLinux()], _stop()]),
        ],
    )


def _textoDirectorioMac():
    return Nodo(
        "_textoDirectorioMac",
        [
            Nodo.Eleccion([_letra(), _digito(), _simboloDirectorioMac()]),
            Nodo.Eleccion([["/", _textoDirectorioMac()], _stop()]),
        ],
    )


# TODO _simboloDirectorioWindows
def _simboloDirectorioWindows():
    return Nodo("_simboloDirectorioWindows", [])


# TODO _simboloDirectorioLinux
def _simboloDirectorioLinux():
    return Nodo("_simboloDirectorioLinux", [])


# TODO _simboloDirectorioMac
def _simboloDirectorioMac():
    return Nodo("_simboloDirectorioMac", [])


def _textoDirectorioWeb():
    return Nodo("_textoDirectorioWeb", [Nodo.Eleccion([_urlWeb(), _urlLocal()])])


def _urlWeb():
    return Nodo(
        "_urlWeb",
        [
            Nodo.Eleccion(["http=//", "https=//"]),
            _textoDirectorioExterno(),
            Nodo.Eleccion([[".", _textoDirectorioExterno()], _stop()]),
            Nodo.Eleccion([[".", _textoDirectorioExterno()], _stop()]),
            Nodo.Eleccion([["/", _directorioExternoRuta()], _stop()]),
            Nodo.Eleccion([["?", _directorioExternoParametros()], _stop()]),
        ],
    )


def _textoDirectorioExterno():
    return Nodo(
        "_textoDirectorioExterno",
        [
            Nodo.Eleccion([_letra(), _digito(), _simboloDirectorioExterno()]),
            Nodo.Eleccion([_textoDirectorioExterno(), _stop()]),
        ],
    )


def _simboloDirectorioExterno():
    return Nodo(
        "_simboloDirectorioExterno",
        [Nodo.Eleccion(["-", "_", ".", "~", "%", "+", "=", "&", "@", "!", "$", "'"])],
    )


def _directorioExternoRuta():
    return Nodo(
        "_directorioExternoRuta",
        [
            _textoDirectorioExterno(),
            Nodo.Eleccion([["/", _directorioExternoRuta()], _stop()]),
        ],
    )


def _directorioExternoParametros():
    return Nodo(
        "_directorioExternoParametros",
        [
            _textoDirectorioExterno(),
            "=",
            _textoDirectorioExterno(),
            Nodo.Eleccion([["&", _directorioExternoParametros()], _stop()]),
        ],
    )


def _urlLocal():
    return Nodo(
        "_urlLocal",
        [
            Nodo.Eleccion(["http=//", "https=//"]),
            Nodo.Eleccion(["localhost", "127.0.0.1", "0.0.0.0", "ipLocal"]),
            Nodo.Eleccion([["=", _puerto()], _stop()]),
            Nodo.Eleccion([["/", _directorioExternoRuta()], _stop()]),
        ],
    )


def _ipLocal():
    return Nodo(
        "_ipLocal",
        [
            _digito(),
            Nodo.Eleccion([_digito(), _stop()]),
            Nodo.Eleccion([_digito(), _stop()]),
            ".",
            _digito(),
            Nodo.Eleccion([_digito(), _stop()]),
            Nodo.Eleccion([_digito(), _stop()]),
            ".",
            _digito(),
            Nodo.Eleccion([_digito(), _stop()]),
            Nodo.Eleccion([_digito(), _stop()]),
            ".",
            _digito(),
            Nodo.Eleccion([_digito(), _stop()]),
            Nodo.Eleccion([_digito(), _stop()]),
        ],
    )


def _puerto():
    return Nodo(
        "_puerto",
        [
            _digito(),
            Nodo.Eleccion([_digito(), _stop()]),
            Nodo.Eleccion([_digito(), _stop()]),
            Nodo.Eleccion([_digito(), _stop()]),
            Nodo.Eleccion([_digito(), _stop()]),
        ],
    )


# TODO _codigoInyectado
def _codigoInyectado():
    return Nodo("_codigoInyectado", [])


def _stop():
    return Nodo("_stop", [""])


###
# TODO _poolStrings
def _poolStrings():
    """
    pool de strings, para ahorrar adn
    a la hora de crear palabras
    """
    return Nodo(
        "_poolStrings",
        [
            Nodo.Eleccion(
                [
                    _computacion(),
                    _sistema(),
                    _logica(),
                    _agentes(),
                    _espacio(),
                    _tiempo(),
                    _percepcion(),
                    _comunicacion(),
                    _cualidades(),
                    _magnitudes(),
                    _procesos(),
                    _procesos_mentales(),
                    _emociones(),
                    _comportamiento(),
                    _mundo(),
                    _biologia(),
                    _fisica(),
                    _matematicas(),
                    _sociedad(),
                    _personas(),
                    _objetos(),
                    _informacion(),
                    _economia(),
                    _lenguaje(),
                    _causalidad(),
                    _incertidumbre(),
                    _objetivos(),
                    _valores(),
                    _relaciones(),
                    _ciclos(),
                    _limites(),
                    _cambio(),
                    _estructura(),
                ]
            )
        ],
    )


def _computacion():
    return Nodo(
        "_computacion",
        [Nodo.Eleccion([_datos(), _operaciones(), _memoria(), _concurrencia()])],
    )


def _datos():
    return Nodo("_datos", [Nodo.Eleccion([_tipos(), _estructuras()])])


def _tipos():
    return Nodo(
        "_tipos",
        [
            Nodo.Eleccion(
                [
                    "entero",
                    "flotante",
                    "booleano",
                    "cadena",
                    "byte",
                    "caracter",
                    "nulo",
                    "indefinido",
                    "simbolo",
                    "referencia",
                    "puntero",
                    "complejo",
                    "racional",
                    "binario",
                    "hexadecimal",
                ]
            )
        ],
    )


def _estructuras():
    return Nodo(
        "_estructuras",
        [
            Nodo.Eleccion(
                [
                    "lista",
                    "array",
                    "diccionario",
                    "conjunto",
                    "tupla",
                    "pila",
                    "cola",
                    "arbol",
                    "grafo",
                    "matriz",
                    "tabla",
                    "heap",
                    "trie",
                    "buffer",
                    "stream",
                ]
            )
        ],
    )


def _operaciones():
    return Nodo("_operaciones", [Nodo.Eleccion([_aritmeticas(), _logicas()])])


def _aritmeticas():
    return Nodo(
        "_aritmeticas",
        [
            Nodo.Eleccion(
                [
                    "suma",
                    "resta",
                    "multiplicacion",
                    "division",
                    "modulo",
                    "potencia",
                    "raiz",
                    "logaritmo",
                    "incremento",
                    "decremento",
                    "negacion",
                    "absoluto",
                    "redondeo",
                    "truncado",
                    "factorial",
                ]
            )
        ],
    )


def _logicas():
    return Nodo(
        "_logicas",
        [
            Nodo.Eleccion(
                [
                    "conjuncion",
                    "disyuncion",
                    "negacion",
                    "implicacion",
                    "equivalencia",
                    "xor",
                    "nand",
                    "nor",
                    "tautologia",
                    "contradiccion",
                    "inferencia",
                    "deduccion",
                    "evaluacion",
                    "cortocircuito",
                    "composicion",
                ]
            )
        ],
    )


def _memoria():
    return Nodo("_memoria", [Nodo.Eleccion([_gestion(), _acceso()])])


def _gestion():
    return Nodo(
        "_gestion",
        [
            Nodo.Eleccion(
                [
                    "asignacion",
                    "liberacion",
                    "recoleccion",
                    "fragmentacion",
                    "compactacion",
                    "paginacion",
                    "segmentacion",
                    "desbordamiento",
                    "fuga",
                    "reutilizacion",
                    "alineacion",
                    "reserva",
                    "pool",
                    "arena",
                    "heap",
                ]
            )
        ],
    )


def _acceso():
    return Nodo(
        "_acceso",
        [
            Nodo.Eleccion(
                [
                    "lectura",
                    "escritura",
                    "cacheo",
                    "indexacion",
                    "desreferencia",
                    "copiado",
                    "movimiento",
                    "intercambio",
                    "mapeo",
                    "volcado",
                    "snapshot",
                    "persistencia",
                    "serializacion",
                    "deserializacion",
                    "clonado",
                ]
            )
        ],
    )


def _concurrencia():
    return Nodo("_concurrencia", [Nodo.Eleccion([_sincronizacion(), _comunicacion()])])


def _sincronizacion():
    return Nodo(
        "_sincronizacion",
        [
            Nodo.Eleccion(
                [
                    "mutex",
                    "semaforo",
                    "barrera",
                    "monitor",
                    "candado",
                    "espera",
                    "señal",
                    "bloqueo",
                    "desbloqueo",
                    "atomico",
                    "exclusion",
                    "seccion",
                    "region",
                    "turno",
                    "orden",
                ]
            )
        ],
    )


def _comunicacion():
    return Nodo(
        "_comunicacion",
        [
            Nodo.Eleccion(
                [
                    "canal",
                    "mensaje",
                    "cola",
                    "pipe",
                    "socket",
                    "evento",
                    "interrupcion",
                    "callback",
                    "promesa",
                    "futuro",
                    "stream",
                    "buffer",
                    "protocolo",
                    "handshake",
                    "broadcast",
                ]
            )
        ],
    )


def _sistema():
    return Nodo(
        "_sistema", [Nodo.Eleccion([_procesos(), _archivos(), _red(), _recursos()])]
    )


def _procesos():
    return Nodo("_procesos", [Nodo.Eleccion([_estados(), _control()])])


def _estados():
    return Nodo(
        "_estados",
        [
            Nodo.Eleccion(
                [
                    "activo",
                    "inactivo",
                    "bloqueado",
                    "esperando",
                    "ejecutando",
                    "terminado",
                    "suspendido",
                    "zombie",
                    "huerfano",
                    "listo",
                    "creado",
                    "detenido",
                    "pausado",
                    "reanudado",
                    "migrado",
                ]
            )
        ],
    )


def _control():
    return Nodo(
        "_control",
        [
            Nodo.Eleccion(
                [
                    "inicio",
                    "fin",
                    "pausa",
                    "reanudacion",
                    "terminacion",
                    "señal",
                    "interrupcion",
                    "prioridad",
                    "planificacion",
                    "asignacion",
                    "migracion",
                    "afinidad",
                    "cuota",
                    "limite",
                    "supervision",
                ]
            )
        ],
    )


def _archivos():
    return Nodo("_archivos", [Nodo.Eleccion([_operaciones_archivos(), _rutas()])])


def _operaciones_archivos():
    return Nodo(
        "_operaciones_archivos",
        [
            Nodo.Eleccion(
                [
                    "apertura",
                    "cierre",
                    "lectura",
                    "escritura",
                    "anexado",
                    "borrado",
                    "copiado",
                    "movimiento",
                    "renombrado",
                    "enlazado",
                    "desenlazado",
                    "sincronizado",
                    "truncado",
                    "bloqueado",
                    "mapeado",
                ]
            )
        ],
    )


def _rutas():
    return Nodo(
        "_rutas",
        [
            Nodo.Eleccion(
                [
                    "absoluta",
                    "relativa",
                    "raiz",
                    "directorio",
                    "subdirectorio",
                    "enlace",
                    "montaje",
                    "particion",
                    "volumen",
                    "ruta",
                    "nombre",
                    "extension",
                    "prefijo",
                    "sufijo",
                    "separador",
                ]
            )
        ],
    )


def _red():
    return Nodo("_red", [Nodo.Eleccion([_protocolos(), _endpoints()])])


def _protocolos():
    return Nodo(
        "_protocolos",
        [
            Nodo.Eleccion(
                [
                    "tcp",
                    "udp",
                    "http",
                    "https",
                    "websocket",
                    "ftp",
                    "ssh",
                    "dns",
                    "dhcp",
                    "icmp",
                    "smtp",
                    "imap",
                    "pop",
                    "rtsp",
                    "mqtt",
                ]
            )
        ],
    )


def _endpoints():
    return Nodo(
        "_endpoints",
        [
            Nodo.Eleccion(
                [
                    "host",
                    "puerto",
                    "socket",
                    "direccion",
                    "interfaz",
                    "gateway",
                    "proxy",
                    "balanceador",
                    "firewall",
                    "router",
                    "switch",
                    "nodo",
                    "cliente",
                    "servidor",
                    "peer",
                ]
            )
        ],
    )


def _recursos():
    return Nodo("_recursos", [Nodo.Eleccion([_tiempo(), _energia()])])


def _tiempo():
    return Nodo(
        "_tiempo",
        [
            Nodo.Eleccion(
                [
                    "tick",
                    "ciclo",
                    "intervalo",
                    "timeout",
                    "deadline",
                    "latencia",
                    "throughput",
                    "jitter",
                    "overhead",
                    "delay",
                    "periodo",
                    "frecuencia",
                    "duracion",
                    "timestamp",
                    "epoch",
                ]
            )
        ],
    )


def _energia():
    return Nodo(
        "_energia",
        [
            Nodo.Eleccion(
                [
                    "consumo",
                    "ahorro",
                    "eficiencia",
                    "coste",
                    "presupuesto",
                    "limite",
                    "umbral",
                    "pico",
                    "base",
                    "reserva",
                    "bateria",
                    "carga",
                    "descarga",
                    "balance",
                    "rendimiento",
                ]
            )
        ],
    )


def _logica():
    return Nodo("_logica", [Nodo.Eleccion([_control(), _evaluacion(), _patrones()])])


def _control():
    return Nodo("_logica", [Nodo.Eleccion([_flujo(), _condiciones()])])


def _flujo():
    return Nodo(
        "_flujo",
        [
            Nodo.Eleccion(
                [
                    "secuencia",
                    "ramificacion",
                    "iteracion",
                    "recursion",
                    "salto",
                    "retorno",
                    "excepcion",
                    "continuacion",
                    "ruptura",
                    "corrutina",
                    "generador",
                    "callback",
                    "evento",
                    "señal",
                    "trampa",
                ]
            )
        ],
    )


def _condiciones():
    return Nodo(
        "_condiciones",
        [
            Nodo.Eleccion(
                [
                    "verdadero",
                    "falso",
                    "nulo",
                    "vacio",
                    "lleno",
                    "igual",
                    "distinto",
                    "mayor",
                    "menor",
                    "contenido",
                    "ausente",
                    "valido",
                    "invalido",
                    "completo",
                    "parcial",
                ]
            )
        ],
    )


def _evaluacion():
    return Nodo("_logica", [Nodo.Eleccion([_comparacion_evaluacion(), _validacion()])])


def _comparacion_evaluacion():
    return Nodo(
        "_comparacion_evaluacion",
        [
            Nodo.Eleccion(
                [
                    "igualdad",
                    "desigualdad",
                    "orden",
                    "inclusion",
                    "interseccion",
                    "union",
                    "diferencia",
                    "subconjunto",
                    "superconjunto",
                    "equivalencia",
                    "similitud",
                    "distancia",
                    "ranking",
                    "clasificacion",
                    "puntuacion",
                ]
            )
        ],
    )


def _validacion():
    return Nodo(
        "_validacion",
        [
            Nodo.Eleccion(
                [
                    "verificacion",
                    "comprobacion",
                    "prueba",
                    "assertion",
                    "invariante",
                    "precondicion",
                    "postcondicion",
                    "restriccion",
                    "regla",
                    "criterio",
                    "filtro",
                    "guard",
                    "contrato",
                    "especificacion",
                    "requisito",
                ]
            )
        ],
    )


def _patrones():
    return Nodo("_logica", [Nodo.Eleccion([_busqueda(), _matching()])])


def _busqueda():
    return Nodo(
        "_busqueda",
        [
            Nodo.Eleccion(
                [
                    "lineal",
                    "binaria",
                    "profundidad",
                    "anchura",
                    "heuristica",
                    "voraz",
                    "exhaustiva",
                    "aleatoria",
                    "dirigida",
                    "incremental",
                    "backtracking",
                    "beam",
                    "hill",
                    "montecarlo",
                    "taboo",
                ]
            )
        ],
    )


def _matching():
    return Nodo(
        "_matching",
        [
            Nodo.Eleccion(
                [
                    "exacto",
                    "parcial",
                    "fuzzy",
                    "regex",
                    "patron",
                    "plantilla",
                    "similitud",
                    "distancia",
                    "prefijo",
                    "sufijo",
                    "substring",
                    "wildcard",
                    "hash",
                    "firma",
                    "huella",
                ]
            )
        ],
    )


def _agentes():
    return Nodo(
        "_agentes",
        [Nodo.Eleccion([_roles(), _relaciones_agentes(), _estados_agentes()])],
    )


def _roles():
    return Nodo("_roles", [Nodo.Eleccion([_activos(), _pasivos()])])


def _activos():
    return Nodo(
        "_activos",
        [
            Nodo.Eleccion(
                [
                    "productor",
                    "consumidor",
                    "iniciador",
                    "coordinador",
                    "supervisor",
                    "ejecutor",
                    "planificador",
                    "explorador",
                    "recolector",
                    "cazador",
                    "guardian",
                    "constructor",
                    "destructor",
                    "optimizador",
                    "adaptador",
                ]
            )
        ],
    )


def _pasivos():
    return Nodo(
        "_pasivos",
        [
            Nodo.Eleccion(
                [
                    "receptor",
                    "almacen",
                    "recurso",
                    "objetivo",
                    "obstaculo",
                    "entorno",
                    "medio",
                    "soporte",
                    "contenedor",
                    "registro",
                    "log",
                    "monitor",
                    "sensor",
                    "actuador",
                    "interfaz",
                ]
            )
        ],
    )


def _relaciones_agentes():
    return Nodo("_relaciones_agentes", [Nodo.Eleccion([_jerarquia(), _dependencia()])])


def _jerarquia():
    return Nodo(
        "_jerarquia",
        [
            Nodo.Eleccion(
                [
                    "padre",
                    "hijo",
                    "hermano",
                    "ancestro",
                    "descendiente",
                    "raiz",
                    "hoja",
                    "nodo",
                    "nivel",
                    "profundidad",
                    "altura",
                    "rango",
                    "posicion",
                    "orden",
                    "subordinado",
                ]
            )
        ],
    )


def _dependencia():
    return Nodo(
        "_dependencia",
        [
            Nodo.Eleccion(
                [
                    "dependiente",
                    "independiente",
                    "acoplado",
                    "desacoplado",
                    "modular",
                    "cohesivo",
                    "abstracto",
                    "concreto",
                    "interfaz",
                    "implementacion",
                    "herencia",
                    "composicion",
                    "delegacion",
                    "inyeccion",
                    "referencia",
                ]
            )
        ],
    )


def _estados_agentes():
    return Nodo("_estados_agentes", [Nodo.Eleccion([_vitales(), _operativos()])])


def _vitales():
    return Nodo(
        "_vitales",
        [
            Nodo.Eleccion(
                [
                    "vivo",
                    "muerto",
                    "naciendo",
                    "muriendo",
                    "reproduciendose",
                    "durmiendo",
                    "activo",
                    "inactivo",
                    "hambriento",
                    "saciado",
                    "sano",
                    "enfermo",
                    "joven",
                    "maduro",
                    "viejo",
                ]
            )
        ],
    )


def _operativos():
    return Nodo(
        "_operativos",
        [
            Nodo.Eleccion(
                [
                    "iniciado",
                    "ejecutando",
                    "esperando",
                    "bloqueado",
                    "terminado",
                    "fallido",
                    "exitoso",
                    "pausado",
                    "reanudado",
                    "migrado",
                    "clonado",
                    "actualizado",
                    "degradado",
                    "recuperado",
                    "estable",
                ]
            )
        ],
    )


def _espacio():
    return Nodo("_espacio", [Nodo.Eleccion([_posicion(), _direccion(), _dimension()])])


def _posicion():
    return Nodo("_posicion", [Nodo.Eleccion([_absoluta(), _relativa_posicion()])])


def _absoluta():
    return Nodo(
        "_absoluta",
        [
            Nodo.Eleccion(
                [
                    "origen",
                    "coordenada",
                    "punto",
                    "ubicacion",
                    "lugar",
                    "sitio",
                    "posicion",
                    "localizacion",
                    "centro",
                    "extremo",
                    "esquina",
                    "borde",
                    "interior",
                    "exterior",
                    "superficie",
                ]
            )
        ],
    )


def _relativa_posicion():
    return Nodo(
        "_relativa_posicion",
        [
            Nodo.Eleccion(
                [
                    "arriba",
                    "abajo",
                    "izquierda",
                    "derecha",
                    "delante",
                    "detras",
                    "cerca",
                    "lejos",
                    "dentro",
                    "fuera",
                    "encima",
                    "debajo",
                    "junto",
                    "entre",
                    "opuesto",
                ]
            )
        ],
    )


def _direccion():
    return Nodo("_direccion", [Nodo.Eleccion([_cardinal(), _relativa_direccion()])])


def _cardinal():
    return Nodo(
        "_cardinal",
        [
            Nodo.Eleccion(
                [
                    "norte",
                    "sur",
                    "este",
                    "oeste",
                    "noreste",
                    "noroeste",
                    "sureste",
                    "suroeste",
                    "vertical",
                    "horizontal",
                    "diagonal",
                    "radial",
                    "tangencial",
                    "axial",
                    "normal",
                ]
            )
        ],
    )


def _relativa_direccion():
    return Nodo(
        "_relativa_direccion",
        [
            Nodo.Eleccion(
                [
                    "adelante",
                    "atras",
                    "lateral",
                    "oblicuo",
                    "perpendicular",
                    "paralelo",
                    "convergente",
                    "divergente",
                    "entrante",
                    "saliente",
                    "ascendente",
                    "descendente",
                    "rotacional",
                    "traslacional",
                    "orbital",
                ]
            )
        ],
    )


def _dimension():
    return Nodo("_dimension", [Nodo.Eleccion([_tamanho(), _distancia])])


def _tamanho():
    return Nodo(
        "_tamanho",
        [
            Nodo.Eleccion(
                [
                    "pequeno",
                    "mediano",
                    "grande",
                    "minimo",
                    "maximo",
                    "infinito",
                    "infinitesimal",
                    "unitario",
                    "doble",
                    "triple",
                    "mitad",
                    "cuarto",
                    "escala",
                    "proporcion",
                    "ratio",
                ]
            )
        ],
    )


def _distancia():
    return Nodo(
        "_distancia",
        [
            Nodo.Eleccion(
                [
                    "cercano",
                    "lejano",
                    "adyacente",
                    "contiguo",
                    "separado",
                    "aislado",
                    "conectado",
                    "alcanzable",
                    "inalcanzable",
                    "limite",
                    "rango",
                    "radio",
                    "diametro",
                    "perimetro",
                    "area",
                ]
            )
        ],
    )


def _tiempo():
    return Nodo("_tiempo", [Nodo.Eleccion([_secuencia(), _duracion(), _frecuencia()])])


def _secuencia():
    return Nodo("_secuencia", [Nodo.Eleccion([_orden(), _fases()])])


def _orden():
    return Nodo(
        "_orden",
        [
            Nodo.Eleccion(
                [
                    "primero",
                    "ultimo",
                    "anterior",
                    "siguiente",
                    "actual",
                    "previo",
                    "posterior",
                    "inicial",
                    "final",
                    "intermedio",
                    "penultimo",
                    "segundo",
                    "tercero",
                    "enésimo",
                    "arbitrario",
                ]
            )
        ],
    )


def _fases():
    return Nodo(
        "_fases",
        [
            Nodo.Eleccion(
                [
                    "inicio",
                    "desarrollo",
                    "fin",
                    "preparacion",
                    "ejecucion",
                    "cierre",
                    "evaluacion",
                    "transicion",
                    "estabilizacion",
                    "degradacion",
                    "recuperacion",
                    "reinicio",
                    "pausa",
                    "reanudacion",
                    "terminacion",
                ]
            )
        ],
    )


def _duracion():
    return Nodo("_duracion", [Nodo.Eleccion([_intervalos(), _limites_duracion()])])


def _intervalos():
    return Nodo(
        "_intervalos",
        [
            Nodo.Eleccion(
                [
                    "instante",
                    "momento",
                    "periodo",
                    "ciclo",
                    "epoch",
                    "tick",
                    "frame",
                    "slot",
                    "ventana",
                    "turno",
                    "ronda",
                    "iteracion",
                    "generacion",
                    "era",
                    "fase",
                ]
            )
        ],
    )


def _limites_duracion():
    return Nodo(
        "_limites_duracion",
        [
            Nodo.Eleccion(
                [
                    "inicio",
                    "fin",
                    "deadline",
                    "timeout",
                    "expiracion",
                    "vencimiento",
                    "limite",
                    "umbral",
                    "maximo",
                    "minimo",
                    "objetivo",
                    "estimacion",
                    "prediccion",
                    "proyeccion",
                    "horizonte",
                ]
            )
        ],
    )


def _frecuencia():
    return Nodo(
        "_frecuencia", [Nodo.Eleccion([_ciclos_frecuencia(), _patrones_frecuencia()])]
    )


def _ciclos_frecuencia():
    return Nodo(
        "_ciclos_frecuencia",
        [
            Nodo.Eleccion(
                [
                    "rapido",
                    "lento",
                    "constante",
                    "variable",
                    "periodico",
                    "aperiodico",
                    "regular",
                    "irregular",
                    "sincronizado",
                    "asincronizado",
                    "continuo",
                    "discreto",
                    "pulsado",
                    "modulado",
                    "adaptativo",
                ]
            )
        ],
    )


def _patrones_frecuencia():
    return Nodo(
        "_patrones_frecuencia",
        [
            Nodo.Eleccion(
                [
                    "diario",
                    "semanal",
                    "mensual",
                    "anual",
                    "horario",
                    "minutal",
                    "segundal",
                    "ciclico",
                    "estacional",
                    "tendencia",
                    "pico",
                    "valle",
                    "plateau",
                    "oscilacion",
                    "deriva",
                ]
            )
        ],
    )


def _percepcion():
    return Nodo(
        "_percepcion", [Nodo.Eleccion([_entrada(), _procesamiento(), _salida()])]
    )


def _entrada():
    return Nodo("_entrada", [Nodo.Eleccion([_senhales(), _eventos()])])


def _senhales():
    return Nodo(
        "_senhales",
        [
            Nodo.Eleccion(
                [
                    "sensor",
                    "detector",
                    "receptor",
                    "antena",
                    "lector",
                    "escaner",
                    "camara",
                    "microfono",
                    "tactil",
                    "termico",
                    "quimico",
                    "electrico",
                    "magnetico",
                    "optico",
                    "acustico",
                ]
            )
        ],
    )


def _eventos():
    return Nodo(
        "_eventos",
        [
            Nodo.Eleccion(
                [
                    "click",
                    "tecla",
                    "movimiento",
                    "colision",
                    "cambio",
                    "activacion",
                    "desactivacion",
                    "conexion",
                    "desconexion",
                    "llegada",
                    "salida",
                    "error",
                    "exito",
                    "timeout",
                    "interrupcion",
                ]
            )
        ],
    )


def _procesamiento():
    return Nodo("_procesamiento", [Nodo.Eleccion([_filtrado(), _clasificacion()])])


def _filtrado():
    return Nodo(
        "_filtrado",
        [
            Nodo.Eleccion(
                [
                    "umbral",
                    "media",
                    "mediana",
                    "maximo",
                    "minimo",
                    "suavizado",
                    "normalizacion",
                    "escalado",
                    "recorte",
                    "muestreo",
                    "interpolacion",
                    "extrapolacion",
                    "reduccion",
                    "compresion",
                    "eliminacion",
                ]
            )
        ],
    )


def _clasificacion():
    return Nodo(
        "_clasificacion",
        [
            Nodo.Eleccion(
                [
                    "categoria",
                    "etiqueta",
                    "clase",
                    "grupo",
                    "cluster",
                    "patron",
                    "anomalia",
                    "outlier",
                    "similitud",
                    "distancia",
                    "probabilidad",
                    "confianza",
                    "precision",
                    "recall",
                    "accuracy",
                ]
            )
        ],
    )


def _salida():
    return Nodo("_salida", [Nodo.Eleccion([_respuestas(), _acciones()])])


def _respuestas():
    return Nodo(
        "_respuestas",
        [
            Nodo.Eleccion(
                [
                    "accion",
                    "reaccion",
                    "respuesta",
                    "señal",
                    "comando",
                    "orden",
                    "instruccion",
                    "movimiento",
                    "parada",
                    "inicio",
                    "ajuste",
                    "correccion",
                    "confirmacion",
                    "rechazo",
                    "ignorar",
                ]
            )
        ],
    )


def _acciones():
    return Nodo(
        "_acciones",
        [
            Nodo.Eleccion(
                [
                    "moverse",
                    "girar",
                    "atacar",
                    "huir",
                    "recoger",
                    "soltar",
                    "comer",
                    "dormir",
                    "comunicar",
                    "explorar",
                    "construir",
                    "destruir",
                    "esperar",
                    "observar",
                    "aprender",
                ]
            )
        ],
    )


def _comunicacion():
    return Nodo(
        "_comunicacion",
        [Nodo.Eleccion([_mensajes(), _canales(), _protocolos_comunicacion()])],
    )


def _mensajes():
    return Nodo("_mensajes", [Nodo.Eleccion([_tipos_mensajes(), _formatos()])])


def _tipos_mensajes():
    return Nodo(
        "_tipos_mensajes",
        [
            Nodo.Eleccion(
                [
                    "solicitud",
                    "respuesta",
                    "notificacion",
                    "alerta",
                    "error",
                    "confirmacion",
                    "rechazo",
                    "consulta",
                    "actualizacion",
                    "broadcast",
                    "unicast",
                    "multicast",
                    "heartbeat",
                    "ping",
                    "ack",
                ]
            )
        ],
    )


def _formatos():
    return Nodo(
        "_formatos",
        [
            Nodo.Eleccion(
                [
                    "texto",
                    "binario",
                    "json",
                    "xml",
                    "csv",
                    "yaml",
                    "protobuf",
                    "avro",
                    "msgpack",
                    "base64",
                    "comprimido",
                    "cifrado",
                    "firmado",
                    "fragmentado",
                    "completo",
                ]
            )
        ],
    )


def _canales():
    return Nodo("_canales", [Nodo.Eleccion([_locales(), _remotos()])])


def _locales():
    return Nodo(
        "_locales",
        [
            Nodo.Eleccion(
                [
                    "pipe",
                    "socket",
                    "memoria",
                    "archivo",
                    "señal",
                    "semaforo",
                    "cola",
                    "buffer",
                    "registro",
                    "variable",
                    "evento",
                    "interrupcion",
                    "callback",
                    "funcion",
                    "metodo",
                ]
            )
        ],
    )


def _remotos():
    return Nodo(
        "_remotos",
        [
            Nodo.Eleccion(
                [
                    "http",
                    "websocket",
                    "tcp",
                    "udp",
                    "grpc",
                    "mqtt",
                    "amqp",
                    "kafka",
                    "redis",
                    "rabbitmq",
                    "zeromq",
                    "nats",
                    "thrift",
                    "rest",
                    "graphql",
                ]
            )
        ],
    )


def _protocolos_comunicacion():
    return Nodo(
        "_protocolos_comunicacion", [Nodo.Eleccion([_sincrono(), _asincrono()])]
    )


def _sincrono():
    return Nodo(
        "_sincrono",
        [
            Nodo.Eleccion(
                [
                    "solicitud",
                    "espera",
                    "respuesta",
                    "timeout",
                    "reintento",
                    "cancelacion",
                    "confirmacion",
                    "validacion",
                    "handshake",
                    "negociacion",
                    "acuerdo",
                    "rechazo",
                    "aceptacion",
                    "cierre",
                    "fin",
                ]
            )
        ],
    )


def _asincrono():
    return Nodo(
        "_asincrono",
        [
            Nodo.Eleccion(
                [
                    "publicacion",
                    "suscripcion",
                    "evento",
                    "callback",
                    "promesa",
                    "futuro",
                    "stream",
                    "cola",
                    "buffer",
                    "notificacion",
                    "señal",
                    "interrupcion",
                    "hook",
                    "trigger",
                    "listener",
                ]
            )
        ],
    )


def _cualidades():
    return Nodo(
        "_cualidades", [Nodo.Eleccion([_rendimiento(), _fiabilidad(), _escala()])]
    )


def _rendimiento():
    return Nodo("_rendimiento", [Nodo.Eleccion([_velocidad(), _eficiencia()])])


def _velocidad():
    return Nodo(
        "_velocidad",
        [
            Nodo.Eleccion(
                [
                    "rapido",
                    "lento",
                    "optimo",
                    "suboptimo",
                    "maximo",
                    "minimo",
                    "promedio",
                    "pico",
                    "base",
                    "sostenido",
                    "instantaneo",
                    "acelerado",
                    "degradado",
                    "estable",
                    "variable",
                ]
            )
        ],
    )


def _eficiencia():
    return Nodo(
        "_eficiencia",
        [
            Nodo.Eleccion(
                [
                    "optimo",
                    "desperdicio",
                    "ahorro",
                    "coste",
                    "beneficio",
                    "ratio",
                    "throughput",
                    "latencia",
                    "overhead",
                    "utilizacion",
                    "saturacion",
                    "cuello",
                    "balance",
                    "distribucion",
                    "paralelismo",
                ]
            )
        ],
    )


def _fiabilidad():
    return Nodo("_fiabilidad", [Nodo.Eleccion([_estabilidad(), _precision()])])


def _estabilidad():
    return Nodo(
        "_estabilidad",
        [
            Nodo.Eleccion(
                [
                    "estable",
                    "inestable",
                    "robusto",
                    "fragil",
                    "resiliente",
                    "tolerante",
                    "redundante",
                    "consistente",
                    "inconsistente",
                    "determinista",
                    "indeterminista",
                    "predecible",
                    "impredecible",
                    "convergente",
                    "divergente",
                ]
            )
        ],
    )


def _precision():
    return Nodo(
        "_precision",
        [
            Nodo.Eleccion(
                [
                    "exacto",
                    "aproximado",
                    "preciso",
                    "impreciso",
                    "correcto",
                    "incorrecto",
                    "valido",
                    "invalido",
                    "completo",
                    "incompleto",
                    "verdadero",
                    "falso",
                    "verificado",
                    "sin_verificar",
                    "confiable",
                ]
            )
        ],
    )


def _escala():
    return Nodo("_escala", [Nodo.Eleccion([_tamanho_escala(), _complejidad()])])


def _tamanho_escala():
    return Nodo(
        "_tamanho_escala",
        [
            Nodo.Eleccion(
                [
                    "pequeno",
                    "mediano",
                    "grande",
                    "minimo",
                    "maximo",
                    "unitario",
                    "masivo",
                    "microscopico",
                    "macroscopico",
                    "local",
                    "global",
                    "distribuido",
                    "centralizado",
                    "jerarquico",
                    "plano",
                ]
            )
        ],
    )


def _complejidad():
    return Nodo(
        "_complejidad",
        [
            Nodo.Eleccion(
                [
                    "simple",
                    "complejo",
                    "trivial",
                    "intricado",
                    "lineal",
                    "cuadratico",
                    "exponencial",
                    "logaritmico",
                    "polinomial",
                    "constante",
                    "amortizado",
                    "peor",
                    "mejor",
                    "promedio",
                    "esperado",
                ]
            )
        ],
    )


def _magnitudes():
    return Nodo("_magnitudes", [Nodo.Eleccion([_cantidad(), _medida(), _limite()])])


def _cantidad():
    return Nodo("_cantidad", [Nodo.Eleccion([_discreta(), _continua()])])


def _discreta():
    return Nodo(
        "_discreta",
        [
            Nodo.Eleccion(
                [
                    "cero",
                    "uno",
                    "pocos",
                    "varios",
                    "muchos",
                    "todos",
                    "ninguno",
                    "alguno",
                    "cada",
                    "par",
                    "impar",
                    "primo",
                    "compuesto",
                    "finito",
                    "infinito",
                ]
            )
        ],
    )


def _continua():
    return Nodo(
        "_continua",
        [
            Nodo.Eleccion(
                [
                    "nulo",
                    "minimo",
                    "bajo",
                    "medio",
                    "alto",
                    "maximo",
                    "negativo",
                    "positivo",
                    "unitario",
                    "normalizado",
                    "escalado",
                    "ponderado",
                    "promedio",
                    "desviacion",
                    "varianza",
                ]
            )
        ],
    )


def _medida():
    return Nodo("_medida", [Nodo.Eleccion([_absoluta_medida(), _relativa()])])


def _absoluta_medida():
    return Nodo(
        "_absoluta_medida",
        [
            Nodo.Eleccion(
                [
                    "longitud",
                    "peso",
                    "volumen",
                    "area",
                    "velocidad",
                    "aceleracion",
                    "fuerza",
                    "energia",
                    "potencia",
                    "temperatura",
                    "presion",
                    "densidad",
                    "frecuencia",
                    "amplitud",
                    "fase",
                ]
            )
        ],
    )


def _relativa():
    return Nodo(
        "_relativa",
        [
            Nodo.Eleccion(
                [
                    "ratio",
                    "porcentaje",
                    "fraccion",
                    "proporcion",
                    "escala",
                    "factor",
                    "coeficiente",
                    "indice",
                    "tasa",
                    "gradiente",
                    "derivada",
                    "integral",
                    "diferencia",
                    "cambio",
                    "delta",
                ]
            )
        ],
    )


def _limite():
    return Nodo("_limite", [Nodo.Eleccion([_minimo(), _maximo()])])


def _minimo():
    return Nodo(
        "_minimo",
        [
            Nodo.Eleccion(
                [
                    "cero",
                    "vacio",
                    "nulo",
                    "base",
                    "suelo",
                    "umbral",
                    "minimo",
                    "inferior",
                    "fondo",
                    "inicio",
                    "origen",
                    "raiz",
                    "nucleo",
                    "esencial",
                    "irreducible",
                ]
            )
        ],
    )


def _maximo():
    return Nodo(
        "_maximo",
        [
            Nodo.Eleccion(
                [
                    "lleno",
                    "saturado",
                    "desbordado",
                    "maximo",
                    "superior",
                    "techo",
                    "limite",
                    "frontera",
                    "capacidad",
                    "umbral",
                    "pico",
                    "cumbre",
                    "extremo",
                    "infinito",
                    "ilimitado",
                ]
            )
        ],
    )


def _procesos():
    return Nodo(
        "_procesos",
        [
            Nodo.Eleccion(
                [_ciclo(), _transformacion(), _control_procesos(), _optimizacion()]
            )
        ],
    )


def _ciclo():
    return Nodo("_ciclo", [Nodo.Eleccion([_inicio(), _fin()])])


def _inicio():
    return Nodo(
        "_inicio",
        [
            Nodo.Eleccion(
                [
                    "arranque",
                    "inicializacion",
                    "activacion",
                    "lanzamiento",
                    "creacion",
                    "instanciacion",
                    "carga",
                    "montaje",
                    "preparacion",
                    "configuracion",
                    "calibracion",
                    "sincronizacion",
                    "conexion",
                    "registro",
                    "arranque",
                ]
            )
        ],
    )


def _fin():
    return Nodo(
        "_fin",
        [
            Nodo.Eleccion(
                [
                    "terminacion",
                    "finalizacion",
                    "cierre",
                    "destruccion",
                    "liberacion",
                    "limpieza",
                    "desmontaje",
                    "desconexion",
                    "guardado",
                    "archivado",
                    "reporte",
                    "log",
                    "señal",
                    "notificacion",
                    "propagacion",
                ]
            )
        ],
    )


def _transformacion():
    return Nodo(
        "_transformacion",
        [Nodo.Eleccion([_entrada_transformacion(), _salida_transformacion()])],
    )


def _entrada_transformacion():
    return Nodo(
        "_entrada_transformacion",
        [
            Nodo.Eleccion(
                [
                    "dato",
                    "señal",
                    "evento",
                    "solicitud",
                    "parametro",
                    "argumento",
                    "recurso",
                    "material",
                    "energia",
                    "informacion",
                    "instruccion",
                    "comando",
                    "configuracion",
                    "estado",
                    "contexto",
                ]
            )
        ],
    )


def _salida_transformacion():
    return Nodo(
        "_salida_transformacion",
        [
            Nodo.Eleccion(
                [
                    "resultado",
                    "respuesta",
                    "producto",
                    "efecto",
                    "señal",
                    "evento",
                    "notificacion",
                    "error",
                    "excepcion",
                    "log",
                    "reporte",
                    "estado",
                    "cambio",
                    "actualizacion",
                    "decision",
                ]
            )
        ],
    )


def _control_procesos():
    return Nodo("_control_procesos", [Nodo.Eleccion([_supervision(), _correccion()])])


def _supervision():
    return Nodo(
        "_supervision",
        [
            Nodo.Eleccion(
                [
                    "monitor",
                    "watchdog",
                    "guardian",
                    "inspector",
                    "auditor",
                    "verificador",
                    "validador",
                    "trazador",
                    "profiler",
                    "debugger",
                    "logger",
                    "sensor",
                    "detector",
                    "analizador",
                    "evaluador",
                ]
            )
        ],
    )


def _correccion():
    return Nodo(
        "_correccion",
        [
            Nodo.Eleccion(
                [
                    "ajuste",
                    "correccion",
                    "compensacion",
                    "calibracion",
                    "normalizacion",
                    "regularizacion",
                    "penalizacion",
                    "recompensa",
                    "retroalimentacion",
                    "adaptacion",
                    "optimizacion",
                    "reparacion",
                    "recuperacion",
                    "reinicio",
                    "rollback",
                ]
            )
        ],
    )


def _optimizacion():
    return Nodo("_optimizacion", [Nodo.Eleccion([_mejora(), _ajuste()])])


def _mejora():
    return Nodo(
        "_mejora",
        [
            Nodo.Eleccion(
                [
                    "incremento",
                    "aceleracion",
                    "eficiencia",
                    "ahorro",
                    "reduccion",
                    "simplificacion",
                    "paralelizacion",
                    "cacheo",
                    "precalculo",
                    "lazy",
                    "eager",
                    "fusion",
                    "eliminacion",
                    "reutilizacion",
                    "especializacion",
                ]
            )
        ],
    )


def _ajuste():
    return Nodo(
        "_ajuste",
        [
            Nodo.Eleccion(
                [
                    "parametro",
                    "hiperparametro",
                    "umbral",
                    "tasa",
                    "factor",
                    "peso",
                    "bias",
                    "regularizacion",
                    "momentum",
                    "decay",
                    "temperatura",
                    "exploracion",
                    "explotacion",
                    "balance",
                    "trade-off",
                ]
            )
        ],
    )


def _procesos_mentales():
    return Nodo(
        "_procesos_mentales",
        [
            Nodo.Eleccion(
                [
                    _cognicion(),
                    _razonamiento(),
                    _aprendizaje(),
                    _decision(),
                    _creatividad(),
                    _metacognicion(),
                ]
            )
        ],
    )


def _cognicion():
    return Nodo("_cognicion", [Nodo.Eleccion([_atencion(), _memoria_cognicion()])])


def _atencion():
    return Nodo(
        "_atencion",
        [
            Nodo.Eleccion(
                [
                    "foco",
                    "concentracion",
                    "seleccion",
                    "filtracion",
                    "priorizacion",
                    "ignorar",
                    "destacar",
                    "seguimiento",
                    "cambio",
                    "division",
                    "sostenida",
                    "alerta",
                    "vigilancia",
                    "orientacion",
                    "deteccion",
                ]
            )
        ],
    )


def _memoria_cognicion():
    return Nodo(
        "_memoria_cognicion",
        [
            Nodo.Eleccion(
                [
                    "almacenamiento",
                    "recuperacion",
                    "codificacion",
                    "consolidacion",
                    "olvido",
                    "reconocimiento",
                    "recuerdo",
                    "asociacion",
                    "indexacion",
                    "busqueda",
                    "cache",
                    "buffer",
                    "registro",
                    "traza",
                    "huella",
                ]
            )
        ],
    )


def _razonamiento():
    return Nodo("_razonamiento", [Nodo.Eleccion([_deduccion(), _induccion()])])


def _deduccion():
    return Nodo(
        "_deduccion",
        [
            Nodo.Eleccion(
                [
                    "inferencia",
                    "conclusion",
                    "premisa",
                    "argumento",
                    "silogismo",
                    "implicacion",
                    "consecuencia",
                    "derivacion",
                    "demostracion",
                    "prueba",
                    "validez",
                    "solidez",
                    "certeza",
                    "necesidad",
                    "suficiencia",
                ]
            )
        ],
    )


def _induccion():
    return Nodo(
        "_induccion",
        [
            Nodo.Eleccion(
                [
                    "generalizacion",
                    "patron",
                    "tendencia",
                    "hipotesis",
                    "probabilidad",
                    "evidencia",
                    "muestra",
                    "sesgo",
                    "error",
                    "incertidumbre",
                    "prediccion",
                    "extrapolacion",
                    "abstraccion",
                    "modelo",
                    "teoria",
                ]
            )
        ],
    )


def _aprendizaje():
    return Nodo("_aprendizaje", [Nodo.Eleccion([_observacion(), _adaptacion()])])


def _observacion():
    return Nodo(
        "_observacion",
        [
            Nodo.Eleccion(
                [
                    "muestra",
                    "ejemplo",
                    "instancia",
                    "dato",
                    "experiencia",
                    "feedback",
                    "señal",
                    "recompensa",
                    "penalizacion",
                    "error",
                    "gradiente",
                    "actualizacion",
                    "convergencia",
                    "divergencia",
                    "plateau",
                ]
            )
        ],
    )


def _adaptacion():
    return Nodo(
        "_adaptacion",
        [
            Nodo.Eleccion(
                [
                    "ajuste",
                    "correccion",
                    "generalizacion",
                    "especializacion",
                    "transferencia",
                    "regularizacion",
                    "robustez",
                    "plasticidad",
                    "estabilidad",
                    "exploracion",
                    "explotacion",
                    "curiosidad",
                    "novedad",
                    "habituacion",
                    "sensibilizacion",
                ]
            )
        ],
    )


def _decision():
    return Nodo("_decision", [Nodo.Eleccion([_evaluacion_decision(), _eleccion()])])


def _evaluacion_decision():
    return Nodo(
        "_evaluacion_decision",
        [
            Nodo.Eleccion(
                [
                    "utilidad",
                    "coste",
                    "beneficio",
                    "riesgo",
                    "probabilidad",
                    "valor",
                    "prioridad",
                    "urgencia",
                    "importancia",
                    "relevancia",
                    "confianza",
                    "incertidumbre",
                    "alternativa",
                    "criterio",
                    "objetivo",
                ]
            )
        ],
    )


def _eleccion():
    return Nodo(
        "_eleccion",
        [
            Nodo.Eleccion(
                [
                    "seleccion",
                    "preferencia",
                    "compromiso",
                    "trade-off",
                    "optimizacion",
                    "satisfaccion",
                    "maximizacion",
                    "minimizacion",
                    "equilibrio",
                    "exploracion",
                    "explotacion",
                    "aleatoria",
                    "greedy",
                    "conservadora",
                    "arriesgada",
                ]
            )
        ],
    )


def _creatividad():
    return Nodo("_creatividad", [Nodo.Eleccion([_generacion(), _combinacion()])])


def _generacion():
    return Nodo(
        "_generacion",
        [
            Nodo.Eleccion(
                [
                    "idea",
                    "hipotesis",
                    "propuesta",
                    "alternativa",
                    "variacion",
                    "mutacion",
                    "combinacion",
                    "recombinacion",
                    "analogia",
                    "metafora",
                    "abstraccion",
                    "generalizacion",
                    "especializacion",
                    "invencion",
                    "descubrimiento",
                ]
            )
        ],
    )


def _combinacion():
    return Nodo(
        "_combinacion",
        [
            Nodo.Eleccion(
                [
                    "mezcla",
                    "fusion",
                    "hibridacion",
                    "cruce",
                    "composicion",
                    "integracion",
                    "sintesis",
                    "emergencia",
                    "sinergia",
                    "conflicto",
                    "tension",
                    "resolucion",
                    "compromiso",
                    "balance",
                    "armonia",
                ]
            )
        ],
    )


def _metacognicion():
    return Nodo("_metacognicion", [Nodo.Eleccion([_reflexion(), _autoregulacion()])])


def _reflexion():
    return Nodo(
        "_reflexion",
        [
            Nodo.Eleccion(
                [
                    "evaluacion",
                    "revision",
                    "critica",
                    "analisis",
                    "introspección",
                    "autoobservacion",
                    "monitoreo",
                    "deteccion",
                    "correccion",
                    "ajuste",
                    "planificacion",
                    "regulacion",
                    "control",
                    "supervision",
                    "auditoria",
                ]
            )
        ],
    )


def _autoregulacion():
    return Nodo(
        "_autoregulacion",
        [
            Nodo.Eleccion(
                [
                    "control",
                    "inhibicion",
                    "activacion",
                    "ajuste",
                    "planificacion",
                    "monitoreo",
                    "evaluacion",
                    "correccion",
                    "adaptacion",
                    "flexibilidad",
                    "persistencia",
                    "abandono",
                    "redireccion",
                    "priorización",
                    "balance",
                ]
            )
        ],
    )


def _emociones():
    return Nodo(
        "_emociones",
        [Nodo.Eleccion([_valencia(), _activacion(), _sociales(), _motivacion()])],
    )


def _valencia():
    return Nodo("_valencia", [Nodo.Eleccion([_positivas(), _negativas()])])


def _positivas():
    return Nodo(
        "_positivas",
        [
            Nodo.Eleccion(
                [
                    "alegria",
                    "satisfaccion",
                    "entusiasmo",
                    "confianza",
                    "esperanza",
                    "gratitud",
                    "orgullo",
                    "amor",
                    "placer",
                    "alivio",
                    "interes",
                    "curiosidad",
                    "asombro",
                    "admiracion",
                    "serenidad",
                ]
            )
        ],
    )


def _negativas():
    return Nodo(
        "_negativas",
        [
            Nodo.Eleccion(
                [
                    "tristeza",
                    "frustacion",
                    "miedo",
                    "ansiedad",
                    "enojo",
                    "disgusto",
                    "verguenza",
                    "culpa",
                    "envidia",
                    "aburrimiento",
                    "confusion",
                    "duda",
                    "desesperanza",
                    "rechazo",
                    "soledad",
                ]
            )
        ],
    )


def _activacion():
    return Nodo("_activacion", [Nodo.Eleccion([_alta(), _baja()])])


def _alta():
    return Nodo(
        "_alta",
        [
            Nodo.Eleccion(
                [
                    "excitacion",
                    "urgencia",
                    "alarma",
                    "panico",
                    "euforia",
                    "furia",
                    "entusiasmo",
                    "alerta",
                    "tension",
                    "estres",
                    "activacion",
                    "energia",
                    "impulso",
                    "motivacion",
                    "aceleracion",
                ]
            )
        ],
    )


def _baja():
    return Nodo(
        "_baja",
        [
            Nodo.Eleccion(
                [
                    "calma",
                    "relajacion",
                    "apatia",
                    "fatiga",
                    "somnolencia",
                    "desinteres",
                    "quietud",
                    "pasividad",
                    "letargo",
                    "agotamiento",
                    "descanso",
                    "recuperacion",
                    "estabilidad",
                    "equilibrio",
                    "serenidad",
                ]
            )
        ],
    )


def _sociales():
    return Nodo("_sociales", [Nodo.Eleccion([
        _empatia(),
        _rechazo()
    ])])
    
def _empatia():
    return Nodo("_empatia", [Nodo.Eleccion([
                "comprension",
        "conexion",
        "resonancia",
        "compasion",
        "altruismo",
        "cooperacion",
        "confianza",
        "lealtad",
        "solidaridad",
        "apoyo",
        "cuidado",
        "respeto",
        "reconocimiento",
        "validacion",
        "aceptacion"
    ])])

def _rechazo():
    return Nodo("_rechazo", [Nodo.Eleccion([
                "exclusion",
        "desconfianza",
        "hostilidad",
        "competencia",
        "rivalidad",
        "envidia",
        "celos",
        "traicion",
        "abandono",
        "aislamiento",
        "marginacion",
        "discriminacion",
        "conflicto",
        "agresion",
        "dominacion"
    ])])


def _motivacion():
    return Nodo("_motivacion", [Nodo.Eleccion([
        _atraccion(),
        _aversion()
    ])])
    
def _atraccion():
    return Nodo("_atraccion", [Nodo.Eleccion([
             "deseo",
        "objetivo",
        "recompensa",
        "incentivo",
        "interes",
        "curiosidad",
        "necesidad",
        "hambre",
        "sed",
        "atraccion",
        "impulso",
        "tendencia",
        "preferencia",
        "valor",
        "utilidad"
    ])])
    
def _aversion():
    return Nodo("_aversion", [Nodo.Eleccion([
                "miedo",
        "evitacion",
        "rechazo",
        "repulsion",
        "amenaza",
        "peligro",
        "dolor",
        "castigo",
        "coste",
        "riesgo",
        "perdida",
        "daño",
        "deterioro",
        "disminucion",
        "fracaso"
    ])])


def _comportamiento():
    return Nodo("_comportamiento", [Nodo.Eleccion([
        _movimiento(),
        _interaccion(),
        _estrategia(),
        _adaptacion_comportamiento()
    ])])

def _movimiento():
    return Nodo("_movimiento", [Nodo.Eleccion([
        _aproximacion(),
        _evitacion()
    ])])
    
def _aproximacion():
    return Nodo("_aproximacion", [Nodo.Eleccion([
         "avance",
        "acercamiento",
        "seguimiento",
        "persecucion",
        "busqueda",
        "atraccion",
        "convergencia",
        "orientacion",
        "navegacion",
        "trayectoria",
        "ruta",
        "camino",
        "direccion",
        "destino",
        "objetivo"
    ])])
    
def _evitacion():
    return Nodo("_evitacion", [Nodo.Eleccion([
         "huida",
        "alejamiento",
        "evasion",
        "desvio",
        "rodeo",
        "esquive",
        "retirada",
        "defensa",
        "proteccion",
        "barrera",
        "obstáculo",
        "repulsion",
        "divergencia",
        "escape",
        "refugio"
    ])])

def _interaccion():
    return Nodo("_interaccion", [Nodo.Eleccion([
        _cooperacion(),
        _competicion()
    ])])
    
def _cooperacion():
    return Nodo("_cooperacion", [Nodo.Eleccion([
            "colaboracion",
        "ayuda",
        "compartir",
        "coordinacion",
        "sincronizacion",
        "alianza",
        "equipo",
        "red",
        "sinergia",
        "mutualismo",
        "intercambio",
        "comunicacion",
        "acuerdo",
        "contrato",
        "protocolo"
    ])])

def _competicion():
    return Nodo("_competicion", [Nodo.Eleccion([
            "rivalidad",
        "disputa",
        "conflicto",
        "lucha",
        "competencia",
        "dominacion",
        "subordinacion",
        "jerarquia",
        "territorio",
        "recurso",
        "acceso",
        "prioridad",
        "ventaja",
        "desventaja",
        "equilibrio"
    ])])

def _estrategia():
    return Nodo("_estrategia", [Nodo.Eleccion([
        _ofensiva(),
        _defensiva()
    ])])
    
def _ofensiva():
    return Nodo("_ofensiva", [Nodo.Eleccion([
             "ataque",
        "expansion",
        "invasion",
        "conquista",
        "dominacion",
        "explotacion",
        "acumulacion",
        "monopolio",
        "ventaja",
        "adelanto",
        "superioridad",
        "iniciativa",
        "agresion",
        "presion",
        "avance"
    ])])
    
def _defensiva():
    return Nodo("_defensiva", [Nodo.Eleccion([
           "defensa",
        "proteccion",
        "conservacion",
        "resistencia",
        "resiliencia",
        "adaptacion",
        "camuflaje",
        "ocultacion",
        "retirada",
        "consolidacion",
        "fortaleza",
        "barrera",
        "escudo",
        "refugio",
        "reserva"
    ])])

def _adaptacion_comportamiento():
    return Nodo("_adaptacion_comportamiento", [Nodo.Eleccion([
        _exploracion(),
        _explotacion()
    ])])
    
def _exploracion():
    return Nodo("_exploracion", [Nodo.Eleccion([
                "busqueda",
        "descubrimiento",
        "novedad",
        "curiosidad",
        "experimentacion",
        "prueba",
        "ensayo",
        "error",
        "aprendizaje",
        "diversificacion",
        "variacion",
        "mutacion",
        "innovacion",
        "riesgo",
        "incertidumbre"
    ])])

def _explotacion():
    return Nodo("_explotacion", [Nodo.Eleccion([
              "uso",
        "aprovechamiento",
        "optimizacion",
        "eficiencia",
        "repeticion",
        "rutina",
        "habito",
        "especializacion",
        "perfeccionamiento",
        "refinamiento",
        "consolidacion",
        "estabilizacion",
        "convergencia",
        "certeza",
        "confianza"
    ])])


def _mundo():
    return Nodo("_mundo", [Nodo.Eleccion([
        _entorno(),
        _recursos_mundo(),
        _fenomenos(),
        _escala_mundo()
    ])])
    
def _entorno():
    return Nodo("_entorno", [Nodo.Eleccion([
        _terreno(),
        _clima()
    ])])
    
def _terreno():
    return Nodo("_terreno", [Nodo.Eleccion([
                "liso",
        "rugoso",
        "plano",
        "elevado",
        "deprimido",
        "solido",
        "liquido",
        "gaseoso",
        "denso",
        "disperso",
        "continuo",
        "discontinuo",
        "homogeneo",
        "heterogeneo",
        "complejo"
    ])])
    
def _clima():
    return Nodo("_clima", [Nodo.Eleccion([
                "calido",
        "frio",
        "templado",
        "humedo",
        "seco",
        "variable",
        "estable",
        "extremo",
        "ciclico",
        "estacional",
        "impredecible",
        "predecible",
        "gradual",
        "abrupto",
        "oscilante"
    ])])
    
def _recursos_mundo():
    return Nodo("_recursos_mundo", [Nodo.Eleccion([
        _naturales(),
        _artificiales()
    ])])
    
def _naturales():
    return Nodo("_naturales", [Nodo.Eleccion([
             "energia",
        "agua",
        "alimento",
        "material",
        "espacio",
        "tiempo",
        "luz",
        "calor",
        "mineral",
        "organico",
        "inorganico",
        "renovable",
        "agotable",
        "abundante",
        "escaso",
        "piedra",
        "rio",
        "mar",
        "comida",
        "fuego",
        
    ])])
    
def _artificiales():
    return Nodo("_artificiales", [Nodo.Eleccion([
             "herramienta",
        "estructura",
        "red",
        "sistema",
        "informacion",
        "conocimiento",
        "tecnologia",
        "infraestructura",
        "servicio",
        "producto",
        "proceso",
        "algoritmo",
        "dato",
        "modelo",
        "programa"
    ])])
    
def _fenomenos():
    return Nodo("_fenomenos", [Nodo.Eleccion([
        _fisicos(),
        _quimicos()
    ])])
    
def _fisicos():
    return Nodo("_fisicos", [Nodo.Eleccion([
                "colision",
        "friccion",
        "gravedad",
        "presion",
        "temperatura",
        "radiacion",
        "campo",
        "onda",
        "resonancia",
        "caos",
        "orden",
        "equilibrio",
        "fluctuacion",
        "transicion",
        "emergencia"
    ])])

def _quimicos():
    return Nodo("_quimicos", [Nodo.Eleccion([
             "reaccion",
        "catalisis",
        "oxidacion",
        "reduccion",
        "sintesis",
        "descomposicion",
        "enlace",
        "ruptura",
        "disolucion",
        "precipitacion",
        "difusion",
        "osmosis",
        "equilibrio",
        "ph",
        "concentracion"
    ])])
    
def _escala_mundo():
    return Nodo("_escala_mundo", [Nodo.Eleccion([
        _micro(),
        _macro()
    ])])
    
def _micro():
    return Nodo("_micro", [Nodo.Eleccion([
                "particula",
        "celula",
        "molecula",
        "átomo",
        "quantum",
        "nano",
        "micro",
        "local",
        "individual",
        "puntual",
        "instantaneo",
        "elemental",
        "basico",
        "primitivo",
        "fundamental"
    ])])

def _macro():
    return Nodo("_macro", [Nodo.Eleccion([
              "sistema",
        "ecosistema",
        "poblacion",
        "red",
        "mundo",
        "global",
        "distribuido",
        "colectivo",
        "emergente",
        "complejo",
        "evolutivo",
        "historico",
        "estadistico",
        "agregado",
        "macroscopico"
    ])])


def _biologia():
    return Nodo("_biologia", [Nodo.Eleccion([
        _organismos(),
        _procesos_biologia(),
        _ecosistema(),
        _evolucion()
    ])])
    
def _organismos():
    return Nodo("_organismos", [Nodo.Eleccion([
        _partes(),
        _funciones_organismos()
    ])])
    
def _partes():
    return Nodo("_partes", [Nodo.Eleccion([
            "celula",
        "tejido",
        "organo",
        "sistema",
        "membrana",
        "nucleo",
        "receptor",
        "efector",
        "sensor",
        "motor",
        "red",
        "canal",
        "puerta",
        "bomba",
        "enzima"
    ])])
    
def _funciones_organismos():
    return Nodo("_funciones_organismos", [Nodo.Eleccion([
           "metabolismo",
        "homeostasis",
        "reproduccion",
        "crecimiento",
        "diferenciacion",
        "apoptosis",
        "comunicacion",
        "movimiento",
        "percepcion",
        "respuesta",
        "regulacion",
        "reparacion",
        "defensa",
        "almacenamiento",
        "transporte"
    ])])
    
def _procesos_biologia():
    return Nodo("_procesos_biologia", [Nodo.Eleccion([
        _metabolismo(),
        _reproduccion()
    ])])
    
def _metabolismo():
    return Nodo("_metabolismo", [Nodo.Eleccion([
            "anabolismo",
        "catabolismo",
        "sintesis",
        "degradacion",
        "oxidacion",
        "reduccion",
        "fosforilacion",
        "glucolisis",
        "respiracion",
        "fermentacion",
        "fotosintesis",
        "ciclo",
        "cadena",
        "gradiente",
        "atp"
    ])])
    
def _reproduccion():
    return Nodo("_reproduccion", [Nodo.Eleccion([
             "division",
        "mitosis",
        "meiosis",
        "fecundacion",
        "diferenciacion",
        "desarrollo",
        "crecimiento",
        "maduracion",
        "senescencia",
        "muerte",
        "regeneracion",
        "clonacion",
        "mutacion",
        "recombinacion",
        "seleccion"
    ])])
    
def _ecosistema():
    return Nodo("_ecosistema", [Nodo.Eleccion([
        _relaciones_ecosistema(),
        _equilibrio()
    ])])
    
def _relaciones_ecosistema():
    return Nodo("_relaciones_ecosistema", [Nodo.Eleccion([
                "depredacion",
        "parasitismo",
        "mutualismo",
        "comensalismo",
        "competencia",
        "simbiosis",
        "cooperacion",
        "facilitacion",
        "inhibicion",
        "cascada",
        "red",
        "flujo",
        "ciclo",
        "equilibrio",
        "perturbacion"
    ])])
    
def _equilibrio():
    return Nodo("_equilibrio", [Nodo.Eleccion([
                "estabilidad",
        "resiliencia",
        "resistencia",
        "recuperacion",
        "sucesion",
        "climax",
        "perturbacion",
        "fluctuacion",
        "oscilacion",
        "regulacion",
        "control",
        "retroalimentacion",
        "homeostasis",
        "adaptacion",
        "evolucion"
    ])])
    
def _evolucion():
    return Nodo("_evolucion", [Nodo.Eleccion([
        _seleccion(),
        _mutacion()
    ])])
    
def _seleccion():
    return Nodo("_seleccion", [Nodo.Eleccion([
                "natural",
        "sexual",
        "artificial",
        "directa",
        "estabilizadora",
        "disruptiva",
        "presion",
        "fitness",
        "adaptacion",
        "ventaja",
        "desventaja",
        "ambiente",
        "nicho",
        "competencia",
        "deriva"
    ])])
    
def _mutacion():
    return Nodo("_mutacion", [Nodo.Eleccion([
             "puntual",
        "insercion",
        "delecion",
        "inversion",
        "transposicion",
        "duplicacion",
        "recombinacion",
        "tasa",
        "neutra",
        "beneficiosa",
        "perjudicial",
        "letal",
        "silenciosa",
        "frameshift",
        "nonsense"
    ])])


def _fisica():
    return Nodo("_fisica", [Nodo.Eleccion([
        
    ])])


def _matematicas():
    return Nodo("_matematicas", [Nodo.Eleccion([])])


def _sociedad():
    return Nodo("_sociedad", [Nodo.Eleccion([])])


def _personas():
    return Nodo("_personas", [Nodo.Eleccion([])])


def _objetos():
    return Nodo("_objetos", [Nodo.Eleccion([])])


def _informacion():
    return Nodo("_informacion", [Nodo.Eleccion([])])


def _economia():
    return Nodo("_economia", [Nodo.Eleccion([])])


def _lenguaje():
    return Nodo("_lenguaje", [Nodo.Eleccion([])])


def _causalidad():
    return Nodo("_causalidad", [Nodo.Eleccion([])])


def _incertidumbre():
    return Nodo("_incertidumbre", [Nodo.Eleccion([])])


def _objetivos():
    return Nodo("_objetivos", [Nodo.Eleccion([])])


def _valores():
    return Nodo("_valores", [Nodo.Eleccion([])])


def _relaciones():
    return Nodo("_relaciones", [Nodo.Eleccion([])])


def _ciclos():
    return Nodo("_ciclos", [Nodo.Eleccion([])])


def _limites():
    return Nodo("_limites", [Nodo.Eleccion([])])


def _cambio():
    return Nodo("_cambio", [Nodo.Eleccion([])])


def _estructura():
    return Nodo("_estructura", [Nodo.Eleccion([])])


guia = {"programa": _programa()}
