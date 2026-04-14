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


###############################################################################
###############################################################################
#
#   /////////   Pool de Strings de conceptos    /////////
#
###############################################################################
###############################################################################
#

#region
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
    return Nodo("_sociales", [Nodo.Eleccion([_empatia(), _rechazo()])])


def _empatia():
    return Nodo(
        "_empatia",
        [
            Nodo.Eleccion(
                [
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
                    "aceptacion",
                ]
            )
        ],
    )


def _rechazo():
    return Nodo(
        "_rechazo",
        [
            Nodo.Eleccion(
                [
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
                    "dominacion",
                ]
            )
        ],
    )


def _motivacion():
    return Nodo("_motivacion", [Nodo.Eleccion([_atraccion(), _aversion()])])


def _atraccion():
    return Nodo(
        "_atraccion",
        [
            Nodo.Eleccion(
                [
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
                    "utilidad",
                ]
            )
        ],
    )


def _aversion():
    return Nodo(
        "_aversion",
        [
            Nodo.Eleccion(
                [
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
                    "fracaso",
                ]
            )
        ],
    )


def _comportamiento():
    return Nodo(
        "_comportamiento",
        [
            Nodo.Eleccion(
                [
                    _movimiento(),
                    _interaccion(),
                    _estrategia(),
                    _adaptacion_comportamiento(),
                ]
            )
        ],
    )


def _movimiento():
    return Nodo("_movimiento", [Nodo.Eleccion([_aproximacion(), _evitacion()])])


def _aproximacion():
    return Nodo(
        "_aproximacion",
        [
            Nodo.Eleccion(
                [
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
                    "objetivo",
                ]
            )
        ],
    )


def _evitacion():
    return Nodo(
        "_evitacion",
        [
            Nodo.Eleccion(
                [
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
                    "refugio",
                ]
            )
        ],
    )


def _interaccion():
    return Nodo("_interaccion", [Nodo.Eleccion([_cooperacion(), _competicion()])])


def _cooperacion():
    return Nodo(
        "_cooperacion",
        [
            Nodo.Eleccion(
                [
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
                    "protocolo",
                ]
            )
        ],
    )


def _competicion():
    return Nodo(
        "_competicion",
        [
            Nodo.Eleccion(
                [
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
                    "equilibrio",
                ]
            )
        ],
    )


def _estrategia():
    return Nodo("_estrategia", [Nodo.Eleccion([_ofensiva(), _defensiva()])])


def _ofensiva():
    return Nodo(
        "_ofensiva",
        [
            Nodo.Eleccion(
                [
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
                    "avance",
                ]
            )
        ],
    )


def _defensiva():
    return Nodo(
        "_defensiva",
        [
            Nodo.Eleccion(
                [
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
                    "reserva",
                ]
            )
        ],
    )


def _adaptacion_comportamiento():
    return Nodo(
        "_adaptacion_comportamiento", [Nodo.Eleccion([_exploracion(), _explotacion()])]
    )


def _exploracion():
    return Nodo(
        "_exploracion",
        [
            Nodo.Eleccion(
                [
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
                    "incertidumbre",
                ]
            )
        ],
    )


def _explotacion():
    return Nodo(
        "_explotacion",
        [
            Nodo.Eleccion(
                [
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
                    "confianza",
                ]
            )
        ],
    )


def _mundo():
    return Nodo(
        "_mundo",
        [Nodo.Eleccion([_entorno(), _recursos_mundo(), _fenomenos(), _escala_mundo()])],
    )


def _entorno():
    return Nodo("_entorno", [Nodo.Eleccion([_terreno(), _clima()])])


def _terreno():
    return Nodo(
        "_terreno",
        [
            Nodo.Eleccion(
                [
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
                    "complejo",
                ]
            )
        ],
    )


def _clima():
    return Nodo(
        "_clima",
        [
            Nodo.Eleccion(
                [
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
                    "oscilante",
                ]
            )
        ],
    )


def _recursos_mundo():
    return Nodo("_recursos_mundo", [Nodo.Eleccion([_naturales(), _artificiales()])])


def _naturales():
    return Nodo(
        "_naturales",
        [
            Nodo.Eleccion(
                [
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
                ]
            )
        ],
    )


def _artificiales():
    return Nodo(
        "_artificiales",
        [
            Nodo.Eleccion(
                [
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
                    "programa",
                ]
            )
        ],
    )


def _fenomenos():
    return Nodo("_fenomenos", [Nodo.Eleccion([_fisicos(), _quimicos()])])


def _fisicos():
    return Nodo(
        "_fisicos",
        [
            Nodo.Eleccion(
                [
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
                    "emergencia",
                ]
            )
        ],
    )


def _quimicos():
    return Nodo(
        "_quimicos",
        [
            Nodo.Eleccion(
                [
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
                    "concentracion",
                ]
            )
        ],
    )


def _escala_mundo():
    return Nodo("_escala_mundo", [Nodo.Eleccion([_micro(), _macro()])])


def _micro():
    return Nodo(
        "_micro",
        [
            Nodo.Eleccion(
                [
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
                    "fundamental",
                ]
            )
        ],
    )


def _macro():
    return Nodo(
        "_macro",
        [
            Nodo.Eleccion(
                [
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
                    "macroscopico",
                ]
            )
        ],
    )


def _biologia():
    return Nodo(
        "_biologia",
        [
            Nodo.Eleccion(
                [_organismos(), _procesos_biologia(), _ecosistema(), _evolucion()]
            )
        ],
    )


def _organismos():
    return Nodo("_organismos", [Nodo.Eleccion([_partes(), _funciones_organismos()])])


def _partes():
    return Nodo(
        "_partes",
        [
            Nodo.Eleccion(
                [
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
                    "enzima",
                ]
            )
        ],
    )


def _funciones_organismos():
    return Nodo(
        "_funciones_organismos",
        [
            Nodo.Eleccion(
                [
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
                    "transporte",
                ]
            )
        ],
    )


def _procesos_biologia():
    return Nodo(
        "_procesos_biologia", [Nodo.Eleccion([_metabolismo(), _reproduccion()])]
    )


def _metabolismo():
    return Nodo(
        "_metabolismo",
        [
            Nodo.Eleccion(
                [
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
                    "atp",
                ]
            )
        ],
    )


def _reproduccion():
    return Nodo(
        "_reproduccion",
        [
            Nodo.Eleccion(
                [
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
                    "seleccion",
                ]
            )
        ],
    )


def _ecosistema():
    return Nodo(
        "_ecosistema", [Nodo.Eleccion([_relaciones_ecosistema(), _equilibrio()])]
    )


def _relaciones_ecosistema():
    return Nodo(
        "_relaciones_ecosistema",
        [
            Nodo.Eleccion(
                [
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
                    "perturbacion",
                ]
            )
        ],
    )


def _equilibrio():
    return Nodo(
        "_equilibrio",
        [
            Nodo.Eleccion(
                [
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
                    "evolucion",
                ]
            )
        ],
    )


def _evolucion():
    return Nodo("_evolucion", [Nodo.Eleccion([_seleccion(), _mutacion()])])


def _seleccion():
    return Nodo(
        "_seleccion",
        [
            Nodo.Eleccion(
                [
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
                    "deriva",
                ]
            )
        ],
    )


def _mutacion():
    return Nodo(
        "_mutacion",
        [
            Nodo.Eleccion(
                [
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
                    "nonsense",
                ]
            )
        ],
    )


def _fisica():
    return Nodo(
        "_fisica",
        [
            Nodo.Eleccion(
                [_materia(), _energia_fisica(), _fuerzas(), _movimiento_fisica()]
            )
        ],
    )


def _materia():
    return Nodo("_materia", [Nodo.Eleccion([_estados_materia(), _propiedades()])])


def _estados_materia():
    return Nodo(
        "_estados_materia",
        [
            Nodo.Eleccion(
                [
                    "solido",
                    "liquido",
                    "gaseoso",
                    "plasma",
                    "condensado",
                    "cristalino",
                    "amorfo",
                    "fluido",
                    "rigido",
                    "elastico",
                    "plastico",
                    "viscoso",
                    "compresible",
                    "incompresible",
                    "isotropo",
                ]
            )
        ],
    )


def _propiedades():
    return Nodo(
        "_propiedades",
        [
            Nodo.Eleccion(
                [
                    "masa",
                    "densidad",
                    "volumen",
                    "temperatura",
                    "presion",
                    "conductividad",
                    "resistencia",
                    "capacidad",
                    "permeabilidad",
                    "viscosidad",
                    "elasticidad",
                    "dureza",
                    "fragilidad",
                    "ductilidad",
                    "magnetismo",
                ]
            )
        ],
    )


def _energia_fisica():
    return Nodo(
        "_energia_fisica", [Nodo.Eleccion([_tipos_energia_fisica(), _transferencia()])]
    )


def _tipos_energia_fisica():
    return Nodo(
        "_tipos_energia_fisica",
        [
            Nodo.Eleccion(
                [
                    "cinetica",
                    "potencial",
                    "termica",
                    "electrica",
                    "magnetica",
                    "quimica",
                    "nuclear",
                    "radiante",
                    "mecanica",
                    "acustica",
                    "gravitacional",
                    "elastica",
                    "interna",
                    "libre",
                    "total",
                ]
            )
        ],
    )


def _transferencia():
    return Nodo(
        "_transferencia",
        [
            Nodo.Eleccion(
                [
                    "conduccion",
                    "conveccion",
                    "radiacion",
                    "trabajo",
                    "calor",
                    "ondas",
                    "particulas",
                    "campos",
                    "corriente",
                    "flujo",
                    "difusion",
                    "conveccion",
                    "irradiacion",
                    "absorcion",
                    "emision",
                ]
            )
        ],
    )


def _fuerzas():
    return Nodo("_fuerzas", [Nodo.Eleccion([_atraccion_fuerzas(), _repulsion()])])


def _atraccion_fuerzas():
    return Nodo(
        "_atraccion_fuerzas",
        [
            Nodo.Eleccion(
                [
                    "gravedad",
                    "electromagnetismo",
                    "cohesion",
                    "adhesion",
                    "tension",
                    "presion",
                    "friccion_estatica",
                    "enlace",
                    "campo",
                    "potencial",
                    "nuclear_fuerte",
                    "van_der_waals",
                    "magnetismo",
                    "electrostatica",
                    "capilaridad",
                ]
            )
        ],
    )


def _repulsion():
    return Nodo(
        "_repulsion",
        [
            Nodo.Eleccion(
                [
                    "presion",
                    "friccion",
                    "tension",
                    "barrera",
                    "campo",
                    "potencial",
                    "nuclear_debil",
                    "electrostatica",
                    "magnetismo",
                    "exclusion",
                    "rigidez",
                    "resistencia",
                    "impedancia",
                    "reactancia",
                    "inductancia",
                ]
            )
        ],
    )


def _movimiento_fisica():
    return Nodo(
        "_movimiento_fisica",
        [Nodo.Eleccion([_velocidad_movimiento_fisica(), _aceleracion])],
    )


def _velocidad_movimiento_fisica():
    return Nodo(
        "_velocidad_movimiento_fisica",
        [
            Nodo.Eleccion(
                [
                    "reposo",
                    "lento",
                    "rapido",
                    "constante",
                    "variable",
                    "acelerado",
                    "desacelerado",
                    "uniforme",
                    "relativo",
                    "absoluto",
                    "instantaneo",
                    "promedio",
                    "terminal",
                    "critico",
                    "supersonico",
                ]
            )
        ],
    )


def _aceleracion():
    return Nodo(
        "_aceleracion",
        [
            Nodo.Eleccion(
                [
                    "positiva",
                    "negativa",
                    "nula",
                    "constante",
                    "variable",
                    "centripeta",
                    "centrifuga",
                    "tangencial",
                    "normal",
                    "angular",
                    "lineal",
                    "gravitacional",
                    "impulsiva",
                    "continua",
                    "oscilatoria",
                ]
            )
        ],
    )


def _matematicas():
    return Nodo(
        "_matematicas",
        [
            Nodo.Eleccion(
                [_algebra(), _geometria(), _probabilidad(), _optimizacion_matematicas()]
            )
        ],
    )


def _algebra():
    return Nodo(
        "_algebra", [Nodo.Eleccion([_operaciones_algebra(), _estructuras_algebra()])]
    )


def _operaciones_algebra():
    return Nodo(
        "_operaciones_algebra",
        [
            Nodo.Eleccion(
                [
                    "suma",
                    "resta",
                    "multiplicacion",
                    "division",
                    "potencia",
                    "raiz",
                    "logaritmo",
                    "modulo",
                    "factorial",
                    "combinacion",
                    "permutacion",
                    "composicion",
                    "inversa",
                    "transpuesta",
                    "determinante",
                ]
            )
        ],
    )


def _estructuras_algebra():
    return Nodo(
        "_estructuras_algebra",
        [
            Nodo.Eleccion(
                [
                    "grupo",
                    "anillo",
                    "campo",
                    "espacio",
                    "algebra",
                    "modulo",
                    "ideal",
                    "homomorfismo",
                    "isomorfismo",
                    "endomorfismo",
                    "automorfismo",
                    "subgrupo",
                    "cociente",
                    "producto",
                    "suma_directa",
                ]
            )
        ],
    )


def _geometria():
    return Nodo("_geometria", [Nodo.Eleccion([_formas(), _transformaciones()])])


def _formas():
    return Nodo(
        "_formas",
        [
            Nodo.Eleccion(
                [
                    "punto",
                    "linea",
                    "plano",
                    "circulo",
                    "triangulo",
                    "cuadrado",
                    "poligono",
                    "esfera",
                    "cubo",
                    "cilindro",
                    "cono",
                    "elipse",
                    "hiperboloide",
                    "paraboloide",
                    "toroide",
                ]
            )
        ],
    )


def _transformaciones():
    return Nodo(
        "_transformaciones",
        [
            Nodo.Eleccion(
                [
                    "traslacion",
                    "rotacion",
                    "reflexion",
                    "escala",
                    "cizalladura",
                    "proyeccion",
                    "inversion",
                    "homografia",
                    "isometria",
                    "similitud",
                    "afinidad",
                    "topologia",
                    "homeomorfismo",
                    "diffeomorfismo",
                    "embedding",
                ]
            )
        ],
    )


def _probabilidad():
    return Nodo(
        "_probabilidad", [Nodo.Eleccion([_eventos_probabilidad(), _distribuciones()])]
    )


def _eventos_probabilidad():
    return Nodo(
        "_eventos_probabilidad",
        [
            Nodo.Eleccion(
                [
                    "independiente",
                    "dependiente",
                    "mutuamente_exclusivo",
                    "complementario",
                    "exhaustivo",
                    "elemental",
                    "compuesto",
                    "condicionado",
                    "conjunto",
                    "union",
                    "interseccion",
                    "diferencia",
                    "simetrico",
                    "probable",
                    "improbable",
                ]
            )
        ],
    )


def _distribuciones():
    return Nodo(
        "_distribuciones",
        [
            Nodo.Eleccion(
                [
                    "uniforme",
                    "normal",
                    "binomial",
                    "poisson",
                    "exponencial",
                    "gamma",
                    "beta",
                    "chi_cuadrado",
                    "t_student",
                    "cauchy",
                    "laplace",
                    "geometric",
                    "hipergeometrica",
                    "multinomial",
                    "dirichlet",
                ]
            )
        ],
    )


def _optimizacion_matematicas():
    return Nodo("_optimizacion_matematicas", [Nodo.Eleccion([_maximos(), _minimos()])])


def _maximos():
    return Nodo(
        "_maximos",
        [
            Nodo.Eleccion(
                [
                    "global",
                    "local",
                    "absoluto",
                    "relativo",
                    "restringido",
                    "libre",
                    "convexo",
                    "no_convexo",
                    "suave",
                    "discontinuo",
                    "aproximado",
                    "exacto",
                    "numerico",
                    "analitico",
                    "heuristico",
                ]
            )
        ],
    )


def _minimos():
    return Nodo(
        "_minimos",
        [
            Nodo.Eleccion(
                [
                    "global",
                    "local",
                    "absoluto",
                    "relativo",
                    "restringido",
                    "libre",
                    "convexo",
                    "no_convexo",
                    "suave",
                    "discontinuo",
                    "aproximado",
                    "exacto",
                    "numerico",
                    "analitico",
                    "heuristico",
                ]
            )
        ],
    )


def _sociedad():
    return Nodo(
        "_sociedad",
        [
            Nodo.Eleccion(
                [
                    _estructura_sociedad(),
                    _interaccion_sociedad(),
                    _recursos_sociedad(),
                    _normas(),
                ]
            )
        ],
    )


def _estructura_sociedad():
    return Nodo(
        "_estructura_sociedad",
        [
            Nodo.Eleccion(
                [_jerarquia_estructura_sociedad(), _roles_estructura_sociedad()]
            )
        ],
    )


def _jerarquia_estructura_sociedad():
    return Nodo(
        "_jerarquia_estructura_sociedad",
        [
            Nodo.Eleccion(
                [
                    "lider",
                    "subordinado",
                    "igual",
                    "superior",
                    "inferior",
                    "rango",
                    "nivel",
                    "estrato",
                    "clase",
                    "casta",
                    "elite",
                    "base",
                    "nucleo",
                    "periferia",
                    "frontera",
                ]
            )
        ],
    )


def _roles_estructura_sociedad():
    return Nodo(
        "_roles_estructura_sociedad",
        [
            Nodo.Eleccion(
                [
                    "productor",
                    "consumidor",
                    "distribuidor",
                    "regulador",
                    "coordinador",
                    "mediador",
                    "guardián",
                    "innovador",
                    "seguidor",
                    "disidente",
                    "especialista",
                    "generalista",
                    "experto",
                    "novato",
                    "observador",
                ]
            )
        ],
    )


def _interaccion_sociedad():
    return Nodo(
        "_interaccion_sociedad",
        [Nodo.Eleccion([_cooperacion_interaccion_sociedad(), _conflicto()])],
    )


def _cooperacion_interaccion_sociedad():
    return Nodo(
        "_cooperacion_interaccion_sociedad",
        [
            Nodo.Eleccion(
                [
                    "alianza",
                    "coalicion",
                    "equipo",
                    "red",
                    "comunidad",
                    "gremio",
                    "colectivo",
                    "asociacion",
                    "colaboracion",
                    "sinergia",
                    "intercambio",
                    "mutualismo",
                    "solidaridad",
                    "ayuda",
                    "apoyo",
                ]
            )
        ],
    )


def _conflicto():
    return Nodo(
        "_conflicto",
        [
            Nodo.Eleccion(
                [
                    "competencia",
                    "rivalidad",
                    "disputa",
                    "guerra",
                    "negociacion",
                    "mediacion",
                    "arbitraje",
                    "compromiso",
                    "victoria",
                    "derrota",
                    "empate",
                    "rendicion",
                    "resistencia",
                    "sabotaje",
                    "traicion",
                ]
            )
        ],
    )


def _recursos_sociedad():
    return Nodo(
        "_recursos_sociedad", [Nodo.Eleccion([_distribucion(), _competencia()])]
    )


def _distribucion():
    return Nodo(
        "_distribucion",
        [
            Nodo.Eleccion(
                [
                    "equitativa",
                    "desigual",
                    "centralizada",
                    "descentralizada",
                    "eficiente",
                    "ineficiente",
                    "justa",
                    "injusta",
                    "optima",
                    "suboptima",
                    "escasa",
                    "abundante",
                    "controlada",
                    "libre",
                    "regulada",
                ]
            )
        ],
    )


def _competencia():
    return Nodo(
        "_competencia",
        [
            Nodo.Eleccion(
                [
                    "monopolio",
                    "oligopolio",
                    "competencia",
                    "libre-mercado",
                    "regulacion",
                    "proteccion",
                    "subsidio",
                    "impuesto",
                    "barrera",
                    "acceso",
                    "exclusion",
                    "inclusion",
                    "prioridad",
                    "asignacion",
                    "racionamiento",
                ]
            )
        ],
    )


def _normas():
    return Nodo("_normas", [Nodo.Eleccion([_reglas(), _sanciones()])])


def _reglas():
    return Nodo(
        "_reglas",
        [
            Nodo.Eleccion(
                [
                    "ley",
                    "norma",
                    "codigo",
                    "protocolo",
                    "convencion",
                    "estandar",
                    "politica",
                    "procedimiento",
                    "restriccion",
                    "permiso",
                    "prohibicion",
                    "obligacion",
                    "recomendacion",
                    "guia",
                    "principio",
                ]
            )
        ],
    )


def _sanciones():
    return Nodo(
        "_sanciones",
        [
            Nodo.Eleccion(
                [
                    "recompensa",
                    "castigo",
                    "incentivo",
                    "desincentivo",
                    "penalizacion",
                    "bonificacion",
                    "reconocimiento",
                    "exclusion",
                    "inclusion",
                    "acceso",
                    "restriccion",
                    "refuerzo",
                    "extincion",
                    "habituacion",
                    "sensibilizacion",
                ]
            )
        ],
    )


def _personas():
    return Nodo(
        "_personas",
        [
            Nodo.Eleccion(
                [
                    _identidad(),
                    _capacidades(),
                    _relaciones_personas(),
                    _estados_personas(),
                ]
            )
        ],
    )


def _identidad():
    return Nodo("_identidad", [Nodo.Eleccion([_nombre(), _rol()])])


def _nombre():
    return Nodo(
        "_nombre",
        [
            Nodo.Eleccion(
                [
                    "identificador",
                    "alias",
                    "etiqueta",
                    "tag",
                    "id",
                    "clave",
                    "referencia",
                    "simbolo",
                    "signo",
                    "marca",
                    "firma",
                    "huella",
                    "token",
                    "codigo",
                    "hash",
                ]
            )
        ],
    )


def _rol():
    return Nodo(
        "_rol",
        [
            Nodo.Eleccion(
                [
                    "agente",
                    "actor",
                    "participante",
                    "observador",
                    "operador",
                    "usuario",
                    "administrador",
                    "creador",
                    "destructor",
                    "mantenedor",
                    "evaluador",
                    "coordinador",
                    "mediador",
                    "guardian",
                    "explorador",
                ]
            )
        ],
    )


def _capacidades():
    return Nodo("_capacidades", [Nodo.Eleccion([_fisicas(), _mentales()])])


def _fisicas():
    return Nodo(
        "_fisicas",
        [
            Nodo.Eleccion(
                [
                    "velocidad",
                    "fuerza",
                    "resistencia",
                    "agilidad",
                    "precision",
                    "alcance",
                    "sensibilidad",
                    "percepcion",
                    "reaccion",
                    "coordinacion",
                    "equilibrio",
                    "orientacion",
                    "navegacion",
                    "manipulacion",
                    "construccion",
                ]
            )
        ],
    )


def _mentales():
    return Nodo(
        "_mentales",
        [
            Nodo.Eleccion(
                [
                    "memoria",
                    "atencion",
                    "razonamiento",
                    "creatividad",
                    "aprendizaje",
                    "planificacion",
                    "decision",
                    "comunicacion",
                    "metacognicion",
                    "abstraccion",
                    "analogia",
                    "inferencia",
                    "prediccion",
                    "evaluacion",
                    "regulacion",
                ]
            )
        ],
    )


def _relaciones_personas():
    return Nodo("_relaciones_personas", [Nodo.Eleccion([_cercanas(), _lejanas()])])


def _cercanas():
    return Nodo(
        "_cercanas",
        [
            Nodo.Eleccion(
                [
                    "aliado",
                    "colaborador",
                    "competidor",
                    "neutral",
                    "conocido",
                    "confiado",
                    "desconfiado",
                    "dependiente",
                    "independiente",
                    "simbiotico",
                    "parasito",
                    "huesped",
                    "vecino",
                    "par",
                    "igual",
                ]
            )
        ],
    )


def _lejanas():
    return Nodo(
        "_lejanas",
        [
            Nodo.Eleccion(
                [
                    "desconocido",
                    "extraño",
                    "enemigo",
                    "indiferente",
                    "potencial",
                    "futuro",
                    "pasado",
                    "historico",
                    "legendario",
                    "mitico",
                    "abstracto",
                    "colectivo",
                    "anonimo",
                    "masivo",
                    "global",
                ]
            )
        ],
    )


def _estados_personas():
    return Nodo(
        "_estados_personas",
        [Nodo.Eleccion([_fisicos_estados_personas(), _mentales_estados_personas()])],
    )


def _fisicos_estados_personas():
    return Nodo(
        "_fisicos_estados_personas",
        [
            Nodo.Eleccion(
                [
                    "activo",
                    "inactivo",
                    "descansando",
                    "moviendo",
                    "comiendo",
                    "durmiendo",
                    "creciendo",
                    "envejeciendo",
                    "sanando",
                    "enfermando",
                    "muriendo",
                    "naciendo",
                    "madurando",
                    "reproduciendose",
                    "evolucionando",
                ]
            )
        ],
    )


def _mentales_estados_personas():
    return Nodo(
        "_mentales_estados_personas",
        [
            Nodo.Eleccion(
                [
                    "alerta",
                    "concentrado",
                    "distraido",
                    "confuso",
                    "claro",
                    "motivado",
                    "desmotivado",
                    "ansioso",
                    "tranquilo",
                    "curioso",
                    "aburrido",
                    "satisfecho",
                    "frustrado",
                    "esperanzado",
                    "desesperado",
                ]
            )
        ],
    )


def _objetos():
    return Nodo(
        "_objetos",
        [
            Nodo.Eleccion(
                [
                    _propiedades_objetos(),
                    _estados_objetos(),
                    _relaciones_objetos(),
                    _usos(),
                ]
            )
        ],
    )


def _propiedades_objetos():
    return Nodo(
        "_propiedades_objetos",
        [Nodo.Eleccion([_fisicas_propiedades_objetos(), _funcionales()])],
    )


def _fisicas_propiedades_objetos():
    return Nodo(
        "_fisicas_propiedades_objetos",
        [
            Nodo.Eleccion(
                [
                    "tamaño",
                    "forma",
                    "peso",
                    "color",
                    "textura",
                    "temperatura",
                    "dureza",
                    "fragilidad",
                    "conductividad",
                    "transparencia",
                    "opacidad",
                    "magnetismo",
                    "elasticidad",
                    "densidad",
                    "viscosidad",
                ]
            )
        ],
    )


def _funcionales():
    return Nodo(
        "_funcionales",
        [
            Nodo.Eleccion(
                [
                    "utilidad",
                    "eficiencia",
                    "durabilidad",
                    "compatibilidad",
                    "modularidad",
                    "escalabilidad",
                    "mantenibilidad",
                    "reparabilidad",
                    "reutilizabilidad",
                    "versatilidad",
                    "especializacion",
                    "precision",
                    "velocidad",
                    "capacidad",
                    "alcance",
                ]
            )
        ],
    )


def _estados_objetos():
    return Nodo("_estados_objetos", [Nodo.Eleccion([_intacto(), _deteriorado()])])


def _intacto():
    return Nodo(
        "_intacto",
        [
            Nodo.Eleccion(
                [
                    "nuevo",
                    "optimo",
                    "funcional",
                    "completo",
                    "limpio",
                    "calibrado",
                    "actualizado",
                    "sincronizado",
                    "disponible",
                    "accesible",
                    "activo",
                    "cargado",
                    "listo",
                    "preparado",
                    "operativo",
                ]
            )
        ],
    )


def _deteriorado():
    return Nodo(
        "_deteriorado",
        [
            Nodo.Eleccion(
                [
                    "roto",
                    "dañado",
                    "desgastado",
                    "obsoleto",
                    "corrupto",
                    "fragmentado",
                    "incompleto",
                    "sucio",
                    "descalibrado",
                    "desactualizado",
                    "inaccesible",
                    "inactivo",
                    "descargado",
                    "bloqueado",
                    "inoperativo",
                ]
            )
        ],
    )


def _relaciones_objetos():
    return Nodo("_relaciones_objetos", [Nodo.Eleccion([_contenedor(), _contenido()])])


def _contenedor():
    return Nodo(
        "_contenedor",
        [
            Nodo.Eleccion(
                [
                    "padre",
                    "entorno",
                    "contexto",
                    "espacio",
                    "contenedor",
                    "sistema",
                    "red",
                    "coleccion",
                    "grupo",
                    "conjunto",
                    "clase",
                    "tipo",
                    "categoria",
                    "dominio",
                    "universo",
                ]
            )
        ],
    )


def _contenido():
    return Nodo(
        "_contenido",
        [
            Nodo.Eleccion(
                [
                    "hijo",
                    "elemento",
                    "componente",
                    "parte",
                    "fragmento",
                    "instancia",
                    "miembro",
                    "item",
                    "entrada",
                    "registro",
                    "nodo",
                    "hoja",
                    "dato",
                    "valor",
                    "referencia",
                ]
            )
        ],
    )


def _usos():
    return Nodo("_usos", [Nodo.Eleccion([_herramienta(), _obstaculo()])])


def _herramienta():
    return Nodo(
        "_herramienta",
        [
            Nodo.Eleccion(
                [
                    "sensor",
                    "actuador",
                    "procesador",
                    "almacen",
                    "transmisor",
                    "receptor",
                    "convertidor",
                    "amplificador",
                    "filtro",
                    "transformador",
                    "generador",
                    "consumidor",
                    "regulador",
                    "controlador",
                    "interfaz",
                ]
            )
        ],
    )


def _obstaculo():
    return Nodo(
        "_obstaculo",
        [
            Nodo.Eleccion(
                [
                    "barrera",
                    "bloqueo",
                    "restriccion",
                    "limite",
                    "frontera",
                    "resistencia",
                    "impedancia",
                    "friccion",
                    "ruido",
                    "interferencia",
                    "perturbacion",
                    "error",
                    "fallo",
                    "anomalia",
                    "excepcion",
                ]
            )
        ],
    )


def _informacion():
    return Nodo(
        "_informacion",
        [
            Nodo.Eleccion(
                [_representacion(), _organizacion(), _flujo_informacion(), _calidad()]
            )
        ],
    )


def _representacion():
    return Nodo("_representacion", [Nodo.Eleccion([_simbolos(), _señales()])])


def _simbolos():
    return Nodo(
        "_simbolos",
        [
            Nodo.Eleccion(
                [
                    "bit",
                    "byte",
                    "caracter",
                    "palabra",
                    "token",
                    "codigo",
                    "signo",
                    "señal",
                    "patron",
                    "estructura",
                    "formato",
                    "esquema",
                    "plantilla",
                    "modelo",
                    "abstraccion",
                ]
            )
        ],
    )


def _señales():
    return Nodo(
        "_señales",
        [
            Nodo.Eleccion(
                [
                    "analogica",
                    "digital",
                    "continua",
                    "discreta",
                    "modulada",
                    "codificada",
                    "comprimida",
                    "cifrada",
                    "firmada",
                    "autenticada",
                    "verificada",
                    "validada",
                    "redundante",
                    "corregida",
                    "integridad",
                ]
            )
        ],
    )


def _organizacion():
    return Nodo(
        "_organizacion",
        [Nodo.Eleccion([_jerarquia_organizacion(), _red_organizacion()])],
    )


def _jerarquia_organizacion():
    return Nodo(
        "_jerarquia_organizacion",
        [
            Nodo.Eleccion(
                [
                    "raiz",
                    "nivel",
                    "profundidad",
                    "rama",
                    "hoja",
                    "nodo",
                    "padre",
                    "hijo",
                    "ancestro",
                    "descendiente",
                    "subárbol",
                    "camino",
                    "frontera",
                    "altura",
                    "anchura",
                ]
            )
        ],
    )


def _red_organizacion():
    return Nodo(
        "_red_organizacion",
        [
            Nodo.Eleccion(
                [
                    "nodo",
                    "enlace",
                    "camino",
                    "ciclo",
                    "componente",
                    "cluster",
                    "hub",
                    "puente",
                    "corte",
                    "flujo",
                    "capacidad",
                    "latencia",
                    "ancho",
                    "distancia",
                    "centralidad",
                ]
            )
        ],
    )


def _flujo_informacion():
    return Nodo("_flujo_informacion", [Nodo.Eleccion([_fuente(), _destino()])])


def _fuente():
    return Nodo(
        "_fuente",
        [
            Nodo.Eleccion(
                [
                    "origen",
                    "emisor",
                    "productor",
                    "generador",
                    "creador",
                    "publicador",
                    "escritor",
                    "proveedor",
                    "servidor",
                    "maestro",
                    "primario",
                    "activo",
                    "push",
                    "iniciador",
                    "trigger",
                ]
            )
        ],
    )


def _destino():
    return Nodo(
        "_destino",
        [
            Nodo.Eleccion(
                [
                    "receptor",
                    "consumidor",
                    "suscriptor",
                    "lector",
                    "cliente",
                    "esclavo",
                    "secundario",
                    "pasivo",
                    "pull",
                    "buffer",
                    "cola",
                    "almacen",
                    "archivo",
                    "log",
                    "registro",
                ]
            )
        ],
    )


def _calidad():
    return Nodo("_calidad", [Nodo.Eleccion([_precision_calidad(), _completitud()])])


def _precision_calidad():
    return Nodo(
        "_precision_calidad",
        [
            Nodo.Eleccion(
                [
                    "exacto",
                    "aproximado",
                    "correcto",
                    "incorrecto",
                    "valido",
                    "invalido",
                    "verificado",
                    "sin_verificar",
                    "confiable",
                    "no_confiable",
                    "completo",
                    "incompleto",
                    "consistente",
                    "inconsistente",
                    "actualizado",
                ]
            )
        ],
    )


def _completitud():
    return Nodo(
        "_completitud",
        [
            Nodo.Eleccion(
                [
                    "completo",
                    "parcial",
                    "total",
                    "fragmentado",
                    "resumido",
                    "detallado",
                    "minimo",
                    "maximo",
                    "suficiente",
                    "insuficiente",
                    "redundante",
                    "escaso",
                    "denso",
                    "disperso",
                    "representativo",
                ]
            )
        ],
    )


def _economia():
    return Nodo(
        "_economia",
        [
            Nodo.Eleccion(
                [
                    _recursos_economia(),
                    _intercambio(),
                    _estrategia_economia(),
                    _equilibrio_economia(),
                ]
            )
        ],
    )


def _recursos_economia():
    return Nodo("_recursos_economia", [Nodo.Eleccion([_escasez(), _abundancia()])])


def _escasez():
    return Nodo(
        "_escasez",
        [
            Nodo.Eleccion(
                [
                    "limitado",
                    "agotable",
                    "finito",
                    "renovable",
                    "no_renovable",
                    "critico",
                    "esencial",
                    "prescindible",
                    "sustituible",
                    "insustituible",
                    "escaso",
                    "raro",
                    "comun",
                    "abundante",
                    "inagotable",
                ]
            )
        ],
    )


def _abundancia():
    return Nodo(
        "_abundancia",
        [
            Nodo.Eleccion(
                [
                    "ilimitado",
                    "inagotable",
                    "excedente",
                    "surplus",
                    "reserva",
                    "acumulado",
                    "almacenado",
                    "disponible",
                    "accesible",
                    "libre",
                    "gratuito",
                    "comun",
                    "publico",
                    "compartido",
                    "abierto",
                ]
            )
        ],
    )


def _intercambio():
    return Nodo("_intercambio", [Nodo.Eleccion([_coste(), _beneficio()])])


def _coste():
    return Nodo(
        "_coste",
        [
            Nodo.Eleccion(
                [
                    "precio",
                    "valor",
                    "coste",
                    "gasto",
                    "inversion",
                    "penalizacion",
                    "tributo",
                    "impuesto",
                    "tarifa",
                    "tasa",
                    "cuota",
                    "deuda",
                    "credito",
                    "interes",
                    "descuento",
                ]
            )
        ],
    )


def _beneficio():
    return Nodo(
        "_beneficio",
        [
            Nodo.Eleccion(
                [
                    "ganancia",
                    "retorno",
                    "utilidad",
                    "valor",
                    "recompensa",
                    "incentivo",
                    "bonus",
                    "dividendo",
                    "interes",
                    "apreciacion",
                    "rendimiento",
                    "eficiencia",
                    "ahorro",
                    "ventaja",
                    "oportunidad",
                ]
            )
        ],
    )


def _estrategia_economia():
    return Nodo("_estrategia_economia", [Nodo.Eleccion([_inversion(), _ahorro()])])


def _inversion():
    return Nodo(
        "_inversion",
        [
            Nodo.Eleccion(
                [
                    "acumulacion",
                    "almacenamiento",
                    "reserva",
                    "diversificacion",
                    "especializacion",
                    "expansion",
                    "crecimiento",
                    "desarrollo",
                    "innovacion",
                    "exploracion",
                    "riesgo",
                    "apuesta",
                    "especulacion",
                    "planificacion",
                    "proyeccion",
                ]
            )
        ],
    )


def _ahorro():
    return Nodo(
        "_ahorro",
        [
            Nodo.Eleccion(
                [
                    "conservacion",
                    "eficiencia",
                    "reduccion",
                    "optimizacion",
                    "reutilizacion",
                    "reciclaje",
                    "minimizacion",
                    "frugalidad",
                    "prudencia",
                    "reserva",
                    "buffer",
                    "margen",
                    "seguridad",
                    "contingencia",
                    "prevision",
                ]
            )
        ],
    )


def _equilibrio_economia():
    return Nodo("_equilibrio_economia", [Nodo.Eleccion([_oferta(), _demanda()])])


def _oferta():
    return Nodo(
        "_oferta",
        [
            Nodo.Eleccion(
                [
                    "produccion",
                    "generacion",
                    "provision",
                    "suministro",
                    "disponibilidad",
                    "capacidad",
                    "inventario",
                    "stock",
                    "reserva",
                    "excedente",
                    "deficit",
                    "escasez",
                    "abundancia",
                    "flujo",
                    "tasa",
                ]
            )
        ],
    )


def _demanda():
    return Nodo(
        "_demanda",
        [
            Nodo.Eleccion(
                [
                    "consumo",
                    "uso",
                    "necesidad",
                    "deseo",
                    "solicitud",
                    "peticion",
                    "requerimiento",
                    "preferencia",
                    "prioridad",
                    "urgencia",
                    "dependencia",
                    "addiction",
                    "habito",
                    "patron",
                    "tendencia",
                ]
            )
        ],
    )


def _lenguaje():
    return Nodo(
        "_lenguaje",
        [
            Nodo.Eleccion(
                [
                    _estructura_lenguaje(),
                    _uso(),
                    _comunicacion_lenguaje(),
                    _representacion_lenguaje(),
                ]
            )
        ],
    )


def _estructura_lenguaje():
    return Nodo("_estructura_lenguaje", [Nodo.Eleccion([_sintaxis(), _semantica()])])


def _sintaxis():
    return Nodo(
        "_sintaxis",
        [
            Nodo.Eleccion(
                [
                    "regla",
                    "gramatica",
                    "produccion",
                    "derivacion",
                    "token",
                    "terminal",
                    "no_terminal",
                    "simbolo",
                    "expresion",
                    "sentencia",
                    "clausula",
                    "predicado",
                    "argumento",
                    "modificador",
                    "conector",
                ]
            )
        ],
    )


def _semantica():
    return Nodo(
        "_semantica",
        [
            Nodo.Eleccion(
                [
                    "significado",
                    "referencia",
                    "denotacion",
                    "connotacion",
                    "contexto",
                    "interpretacion",
                    "ambiguedad",
                    "sinonimo",
                    "antonimo",
                    "hiperonimo",
                    "hiponimo",
                    "meronimo",
                    "metafora",
                    "metonimia",
                    "pragmatica",
                ]
            )
        ],
    )


def _uso():
    return Nodo("_uso", [Nodo.Eleccion([_descripcion(), _instruccion()])])


def _descripcion():
    return Nodo(
        "_descripcion",
        [
            Nodo.Eleccion(
                [
                    "nombre",
                    "etiqueta",
                    "identificador",
                    "definicion",
                    "descripcion",
                    "especificacion",
                    "caracterizacion",
                    "clasificacion",
                    "categoria",
                    "tipo",
                    "instancia",
                    "ejemplo",
                    "contraejemplo",
                    "analogia",
                    "metafora",
                ]
            )
        ],
    )


def _instruccion():
    return Nodo(
        "_instruccion",
        [
            Nodo.Eleccion(
                [
                    "comando",
                    "orden",
                    "instruccion",
                    "directiva",
                    "procedimiento",
                    "algoritmo",
                    "receta",
                    "protocolo",
                    "guia",
                    "regla",
                    "norma",
                    "restriccion",
                    "permiso",
                    "prohibicion",
                    "recomendacion",
                ]
            )
        ],
    )


def _comunicacion_lenguaje():
    return Nodo("_comunicacion_lenguaje", [Nodo.Eleccion([_emisor(), _receptor()])])


def _emisor():
    return Nodo(
        "_emisor",
        [
            Nodo.Eleccion(
                [
                    "hablante",
                    "escritor",
                    "codificador",
                    "transmisor",
                    "fuente",
                    "autor",
                    "creador",
                    "generador",
                    "publicador",
                    "difusor",
                    "iniciador",
                    "provocador",
                    "respondedor",
                    "interlocutor",
                    "narrador",
                ]
            )
        ],
    )


def _receptor():
    return Nodo(
        "_receptor",
        [
            Nodo.Eleccion(
                [
                    "oyente",
                    "lector",
                    "decodificador",
                    "receptor",
                    "destino",
                    "audiencia",
                    "publico",
                    "interprete",
                    "procesador",
                    "evaluador",
                    "critico",
                    "respondedor",
                    "interlocutor",
                    "participante",
                    "observador",
                ]
            )
        ],
    )


def _representacion_lenguaje():
    return Nodo(
        "_representacion_lenguaje",
        [Nodo.Eleccion([_simbolo_representacion_lenguaje(), _referente()])],
    )


def _simbolo_representacion_lenguaje():
    return Nodo(
        "_simbolo_representacion_lenguaje",
        [
            Nodo.Eleccion(
                [
                    "signo",
                    "icono",
                    "indice",
                    "señal",
                    "codigo",
                    "token",
                    "marca",
                    "huella",
                    "traza",
                    "firma",
                    "hash",
                    "identificador",
                    "referencia",
                    "puntero",
                    "enlace",
                ]
            )
        ],
    )


def _referente():
    return Nodo(
        "_referente",
        [
            Nodo.Eleccion(
                [
                    "objeto",
                    "concepto",
                    "entidad",
                    "proceso",
                    "relacion",
                    "propiedad",
                    "estado",
                    "evento",
                    "accion",
                    "situacion",
                    "contexto",
                    "mundo",
                    "modelo",
                    "abstraccion",
                    "idea",
                ]
            )
        ],
    )


def _causalidad():
    return Nodo(
        "_causalidad",
        [
            Nodo.Eleccion(
                [
                    _relaciones_causalidad(),
                    _cadenas(),
                    _probabilidad_causalidad(),
                    _intervencion(),
                ]
            )
        ],
    )


def _relaciones_causalidad():
    return Nodo("_relaciones_causalidad", [Nodo.Eleccion([_causa(), _efecto()])])


def _causa():
    return Nodo(
        "_causa",
        [
            Nodo.Eleccion(
                [
                    "origen",
                    "fuente",
                    "raiz",
                    "trigger",
                    "detonante",
                    "factor",
                    "condicion",
                    "antecedente",
                    "pre-requisito",
                    "necesario",
                    "suficiente",
                    "contribuyente",
                    "inhibidor",
                    "catalizador",
                    "amplificador",
                ]
            )
        ],
    )


def _efecto():
    return Nodo(
        "_efecto",
        [
            Nodo.Eleccion(
                [
                    "resultado",
                    "consecuencia",
                    "impacto",
                    "cambio",
                    "transformacion",
                    "respuesta",
                    "reaccion",
                    "salida",
                    "producto",
                    "efecto",
                    "derivado",
                    "secundario",
                    "colateral",
                    "cascada",
                    "propagacion",
                ]
            )
        ],
    )


def _cadenas():
    return Nodo("_cadenas", [Nodo.Eleccion([_directa(), _indirecta()])])


def _directa():
    return Nodo(
        "_directa",
        [
            Nodo.Eleccion(
                [
                    "inmediata",
                    "proxima",
                    "directa",
                    "lineal",
                    "simple",
                    "obvia",
                    "determinista",
                    "predecible",
                    "controlable",
                    "reversible",
                    "observable",
                    "medible",
                    "cuantificable",
                    "trazable",
                    "verificable",
                ]
            )
        ],
    )


def _indirecta():
    return Nodo(
        "_indirecta",
        [
            Nodo.Eleccion(
                [
                    "mediada",
                    "lejana",
                    "indirecta",
                    "no_lineal",
                    "compleja",
                    "oculta",
                    "estocastica",
                    "impredecible",
                    "incontrolable",
                    "irreversible",
                    "latente",
                    "emergente",
                    "sistemica",
                    "difusa",
                    "acumulada",
                ]
            )
        ],
    )


def _probabilidad_causalidad():
    return Nodo(
        "_probabilidad_causalidad",
        [Nodo.Eleccion([_certeza(), _incertidumbre_probabilidad_causalidad()])],
    )


def _certeza():
    return Nodo(
        "_certeza",
        [
            Nodo.Eleccion(
                [
                    "determinista",
                    "necesario",
                    "inevitable",
                    "seguro",
                    "garantizado",
                    "cierto",
                    "definido",
                    "absoluto",
                    "completo",
                    "total",
                    "incondicional",
                    "universal",
                    "siempre",
                    "invariable",
                    "constante",
                ]
            )
        ],
    )


def _incertidumbre_probabilidad_causalidad():
    return Nodo(
        "_incertidumbre_probabilidad_causalidad",
        [
            Nodo.Eleccion(
                [
                    "probabilistico",
                    "estocastico",
                    "aleatorio",
                    "posible",
                    "contingente",
                    "condicional",
                    "parcial",
                    "aproximado",
                    "estimado",
                    "incierto",
                    "variable",
                    "dependiente",
                    "contextual",
                    "situacional",
                    "emergente",
                ]
            )
        ],
    )


def _intervencion():
    return Nodo(
        "_intervencion", [Nodo.Eleccion([_control_intervencion(), _influencia()])]
    )


def _control_intervencion():
    return Nodo(
        "_control_intervencion",
        [
            Nodo.Eleccion(
                [
                    "manipulacion",
                    "ajuste",
                    "regulacion",
                    "modificacion",
                    "intervencion",
                    "correccion",
                    "optimizacion",
                    "direccion",
                    "guia",
                    "supervision",
                    "monitoreo",
                    "retroalimentacion",
                    "adaptacion",
                    "aprendizaje",
                    "evolucion",
                ]
            )
        ],
    )


def _influencia():
    return Nodo(
        "_influencia",
        [
            Nodo.Eleccion(
                [
                    "sesgo",
                    "incentivo",
                    "presion",
                    "atraccion",
                    "repulsion",
                    "facilitacion",
                    "inhibicion",
                    "amplificacion",
                    "atenuacion",
                    "modulacion",
                    "sincronizacion",
                    "perturbacion",
                    "estabilizacion",
                    "direccion",
                    "orientacion",
                ]
            )
        ],
    )


def _incertidumbre():
    return Nodo(
        "_incertidumbre",
        [
            Nodo.Eleccion(
                [
                    _tipos_incertidumbre(),
                    _manejo(),
                    _decision_incertidumbre(),
                    _informacion_incertidumbre(),
                ]
            )
        ],
    )


def _tipos_incertidumbre():
    return Nodo("_tipos_incertidumbre", [Nodo.Eleccion([_aleatoria(), _epistemica()])])


def _aleatoria():
    return Nodo(
        "_aleatoria",
        [
            Nodo.Eleccion(
                [
                    "ruido",
                    "varianza",
                    "fluctuacion",
                    "oscilacion",
                    "perturbacion",
                    "error",
                    "desviacion",
                    "dispersion",
                    "heterogeneidad",
                    "variabilidad",
                    "estocasticidad",
                    "aleatoriedad",
                    "caos",
                    "turbulencia",
                    "ruido_blanco",
                ]
            )
        ],
    )


def _epistemica():
    return Nodo(
        "_epistemica",
        [
            Nodo.Eleccion(
                [
                    "ignorancia",
                    "desconocimiento",
                    "modelo_incorrecto",
                    "datos_insuficientes",
                    "sesgo",
                    "ambiguedad",
                    "vaguedad",
                    "imprecision",
                    "aproximacion",
                    "estimacion",
                    "suposicion",
                    "hipotesis",
                    "creencia",
                    "opinion",
                    "conjetura",
                ]
            )
        ],
    )


def _manejo():
    return Nodo("_manejo", [Nodo.Eleccion([_estimacion(), _reduccion()])])


def _estimacion():
    return Nodo(
        "_estimacion",
        [
            Nodo.Eleccion(
                [
                    "media",
                    "mediana",
                    "moda",
                    "varianza",
                    "desviacion",
                    "intervalo",
                    "confianza",
                    "prediccion",
                    "proyeccion",
                    "simulacion",
                    "montecarlo",
                    "bootstrap",
                    "bayesiano",
                    "frecuentista",
                    "aproximacion",
                ]
            )
        ],
    )


def _reduccion():
    return Nodo(
        "_reduccion",
        [
            Nodo.Eleccion(
                [
                    "datos",
                    "experimento",
                    "observacion",
                    "medicion",
                    "muestreo",
                    "prueba",
                    "validacion",
                    "verificacion",
                    "refinamiento",
                    "actualizacion",
                    "aprendizaje",
                    "adaptacion",
                    "convergencia",
                    "especializacion",
                    "precision",
                ]
            )
        ],
    )


def _decision_incertidumbre():
    return Nodo("_decision_incertidumbre", [Nodo.Eleccion([_riesgo(), _cautela()])])


def _riesgo():
    return Nodo(
        "_riesgo",
        [
            Nodo.Eleccion(
                [
                    "probabilidad",
                    "impacto",
                    "severidad",
                    "frecuencia",
                    "exposicion",
                    "vulnerabilidad",
                    "amenaza",
                    "peligro",
                    "coste",
                    "beneficio",
                    "trade-off",
                    "umbral",
                    "tolerancia",
                    "aversion",
                    "neutralidad",
                ]
            )
        ],
    )


def _cautela():
    return Nodo(
        "_cautela",
        [
            Nodo.Eleccion(
                [
                    "conservador",
                    "prudente",
                    "cauteloso",
                    "minmax",
                    "satisficing",
                    "robusto",
                    "redundante",
                    "resiliente",
                    "margen",
                    "buffer",
                    "reserva",
                    "contingencia",
                    "plan_b",
                    "fallback",
                    "hedging",
                ]
            )
        ],
    )


def _informacion_incertidumbre():
    return Nodo(
        "_informacion_incertidumbre", [Nodo.Eleccion([_completa(), _parcial()])]
    )


def _completa():
    return Nodo(
        "_completa",
        [
            Nodo.Eleccion(
                [
                    "perfecta",
                    "total",
                    "exhaustiva",
                    "determinista",
                    "conocida",
                    "observable",
                    "medible",
                    "verificable",
                    "trazable",
                    "reproducible",
                    "consistente",
                    "coherente",
                    "completa",
                    "suficiente",
                    "adecuada",
                ]
            )
        ],
    )


def _parcial():
    return Nodo(
        "_parcial",
        [
            Nodo.Eleccion(
                [
                    "imperfecta",
                    "incompleta",
                    "ruidosa",
                    "sesgada",
                    "limitada",
                    "local",
                    "parcial",
                    "aproximada",
                    "estimada",
                    "incierta",
                    "ambigua",
                    "vaga",
                    "imprecisa",
                    "contradictoria",
                    "insuficiente",
                ]
            )
        ],
    )


def _objetivos():
    return Nodo(
        "_objetivos",
        [Nodo.Eleccion([_tipos_objetivos(), _estado(), _prioridad(), _progreso()])],
    )


def _tipos_objetivos():
    return Nodo("_tipos_objetivos", [Nodo.Eleccion([_inmediatos(), _lejanos()])])


def _inmediatos():
    return Nodo(
        "_inmediatos",
        [
            Nodo.Eleccion(
                [
                    "tarea",
                    "accion",
                    "paso",
                    "subobjetivo",
                    "micro",
                    "local",
                    "inmediato",
                    "tactico",
                    "operacional",
                    "concreto",
                    "especifico",
                    "medible",
                    "alcanzable",
                    "relevante",
                    "temporal",
                ]
            )
        ],
    )


def _lejanos():
    return Nodo(
        "_lejanos",
        [
            Nodo.Eleccion(
                [
                    "meta",
                    "vision",
                    "mision",
                    "estrategia",
                    "macro",
                    "global",
                    "largo_plazo",
                    "aspiracion",
                    "ideal",
                    "abstracto",
                    "general",
                    "ambicioso",
                    "transformador",
                    "sistemico",
                    "evolutivo",
                ]
            )
        ],
    )


def _estado():
    return Nodo("_estado", [Nodo.Eleccion([_activo(), _completado()])])


def _activo():
    return Nodo(
        "_activo",
        [
            Nodo.Eleccion(
                [
                    "pendiente",
                    "en_progreso",
                    "bloqueado",
                    "esperando",
                    "activo",
                    "priorizado",
                    "urgente",
                    "critico",
                    "asignado",
                    "planificado",
                    "iniciado",
                    "retomado",
                    "acelerado",
                    "en_riesgo",
                    "atrasado",
                ]
            )
        ],
    )


def _completado():
    return Nodo(
        "_completado",
        [
            Nodo.Eleccion(
                [
                    "logrado",
                    "exitoso",
                    "fallido",
                    "cancelado",
                    "abandonado",
                    "superado",
                    "obsoleto",
                    "reemplazado",
                    "archivado",
                    "aprendido",
                    "evaluado",
                    "documentado",
                    "reproducible",
                    "escalable",
                    "transferible",
                ]
            )
        ],
    )


def _prioridad():
    return Nodo("_prioridad", [Nodo.Eleccion([_urgente(), _diferible()])])


def _urgente():
    return Nodo(
        "_urgente",
        [
            Nodo.Eleccion(
                [
                    "critico",
                    "inmediato",
                    "vital",
                    "esencial",
                    "imprescindible",
                    "urgente",
                    "prioritario",
                    "primero",
                    "maximo",
                    "tope",
                    "deadline",
                    "bloqueante",
                    "dependencia",
                    "cuello",
                    "bottleneck",
                ]
            )
        ],
    )


def _diferible():
    return Nodo(
        "_diferible",
        [
            Nodo.Eleccion(
                [
                    "secundario",
                    "opcional",
                    "deseable",
                    "conveniente",
                    "eventual",
                    "futuro",
                    "planificado",
                    "postergable",
                    "flexible",
                    "adaptable",
                    "negociable",
                    "ajustable",
                    "diferible",
                    "pausable",
                    "cancelable",
                ]
            )
        ],
    )


def _progreso():
    return Nodo("_progreso", [Nodo.Eleccion([_avance(), _retroceso()])])


def _avance():
    return Nodo(
        "_avance",
        [
            Nodo.Eleccion(
                [
                    "incremento",
                    "mejora",
                    "aceleracion",
                    "optimizacion",
                    "convergencia",
                    "aprendizaje",
                    "crecimiento",
                    "expansion",
                    "consolidacion",
                    "estabilizacion",
                    "refinamiento",
                    "perfeccionamiento",
                    "maduracion",
                    "especializacion",
                    "eficiencia",
                ]
            )
        ],
    )


def _retroceso():
    return Nodo(
        "_retroceso",
        [
            Nodo.Eleccion(
                [
                    "degradacion",
                    "error",
                    "fallo",
                    "retroceso",
                    "divergencia",
                    "inestabilidad",
                    "deterioro",
                    "perdida",
                    "reduccion",
                    "desaceleracion",
                    "bloqueo",
                    "estancamiento",
                    "regresion",
                    "colapso",
                    "reinicio",
                ]
            )
        ],
    )


def _valores():
    return Nodo(
        "_valores",
        [
            Nodo.Eleccion(
                [
                    _utilidad(),
                    _prioridad_valores(),
                    _comparacion_valores(),
                    _cambio_valores(),
                ]
            )
        ],
    )


def _utilidad():
    return Nodo("_utilidad", [Nodo.Eleccion([_alto(), _bajo()])])


def _alto():
    return Nodo(
        "_alto",
        [
            Nodo.Eleccion(
                [
                    "esencial",
                    "critico",
                    "vital",
                    "maximo",
                    "optimo",
                    "eficiente",
                    "efectivo",
                    "valioso",
                    "util",
                    "necesario",
                    "imprescindible",
                    "beneficioso",
                    "productivo",
                    "rentable",
                    "ventajoso",
                ]
            )
        ],
    )


def _bajo():
    return Nodo(
        "_bajo",
        [
            Nodo.Eleccion(
                [
                    "prescindible",
                    "innecesario",
                    "inutil",
                    "costoso",
                    "ineficiente",
                    "contraproducente",
                    "perjudicial",
                    "redundante",
                    "obsoleto",
                    "superfluo",
                    "accesorio",
                    "decorativo",
                    "simbolico",
                    "marginal",
                    "irrelevante",
                ]
            )
        ],
    )


def _prioridad_valores():
    return Nodo("_prioridad_valores", [Nodo.Eleccion([_esencial(), _prescindible()])])


def _esencial():
    return Nodo(
        "_esencial",
        [
            Nodo.Eleccion(
                [
                    "vital",
                    "critico",
                    "necesario",
                    "imprescindible",
                    "fundamental",
                    "basico",
                    "primario",
                    "principal",
                    "central",
                    "nuclear",
                    "core",
                    "minimo",
                    "requerido",
                    "obligatorio",
                    "mandatorio",
                ]
            )
        ],
    )


def _prescindible():
    return Nodo(
        "_prescindible",
        [
            Nodo.Eleccion(
                [
                    "opcional",
                    "secundario",
                    "adicional",
                    "complementario",
                    "auxiliar",
                    "accesorio",
                    "alternativo",
                    "sustituible",
                    "reemplazable",
                    "flexible",
                    "negociable",
                    "ajustable",
                    "variable",
                    "contingente",
                    "condicional",
                ]
            )
        ],
    )


def _comparacion_valores():
    return Nodo("_comparacion_valores", [Nodo.Eleccion([_mejor(), _peor()])])


def _mejor():
    return Nodo(
        "_mejor",
        [
            Nodo.Eleccion(
                [
                    "superior",
                    "optimo",
                    "maximo",
                    "preferido",
                    "dominante",
                    "eficiente",
                    "efectivo",
                    "robusto",
                    "fiable",
                    "preciso",
                    "rapido",
                    "escalable",
                    "mantenible",
                    "simple",
                    "elegante",
                ]
            )
        ],
    )


def _peor():
    return Nodo(
        "_peor",
        [
            Nodo.Eleccion(
                [
                    "inferior",
                    "suboptimo",
                    "minimo",
                    "descartado",
                    "dominado",
                    "ineficiente",
                    "inefectivo",
                    "fragil",
                    "no_fiable",
                    "impreciso",
                    "lento",
                    "no_escalable",
                    "dificil",
                    "complejo",
                    "torpe",
                ]
            )
        ],
    )


def _cambio_valores():
    return Nodo("_cambio_valores", [Nodo.Eleccion([_aumento(), _disminucion()])])


def _aumento():
    return Nodo(
        "_aumento",
        [
            Nodo.Eleccion(
                [
                    "incremento",
                    "crecimiento",
                    "expansion",
                    "amplificacion",
                    "aceleracion",
                    "mejora",
                    "optimizacion",
                    "maximizacion",
                    "escalado",
                    "proliferacion",
                    "multiplicacion",
                    "refuerzo",
                    "consolidacion",
                    "maduracion",
                    "evolucion",
                ]
            )
        ],
    )


def _disminucion():
    return Nodo(
        "_disminucion",
        [
            Nodo.Eleccion(
                [
                    "decremento",
                    "reduccion",
                    "contraccion",
                    "atenuacion",
                    "desaceleracion",
                    "degradacion",
                    "deterioro",
                    "minimizacion",
                    "simplificacion",
                    "eliminacion",
                    "extincion",
                    "colapso",
                    "convergencia",
                    "especializacion",
                    "poda",
                ]
            )
        ],
    )


def _relaciones():
    return Nodo(
        "_relaciones",
        [Nodo.Eleccion([_tipo(), _fuerza(), _direccion_relaciones(), _naturaleza()])],
    )


def _tipo():
    return Nodo("_tipo", [Nodo.Eleccion([_simetrica(), _asimetrica()])])


def _simetrica():
    return Nodo(
        "_simetrica",
        [
            Nodo.Eleccion(
                [
                    "igual",
                    "par",
                    "reciproca",
                    "mutua",
                    "bilateral",
                    "equilibrada",
                    "justa",
                    "fair",
                    "compartida",
                    "cooperativa",
                    "horizontal",
                    "democratica",
                    "consensuada",
                    "negociada",
                    "acordada",
                ]
            )
        ],
    )


def _asimetrica():
    return Nodo(
        "_asimetrica",
        [
            Nodo.Eleccion(
                [
                    "desigual",
                    "unilateral",
                    "jerarquica",
                    "dominante",
                    "subordinada",
                    "dependiente",
                    "parasita",
                    "explotadora",
                    "autoritaria",
                    "vertical",
                    "impuesta",
                    "forzada",
                    "heredada",
                    "estructural",
                    "sistemica",
                ]
            )
        ],
    )


def _fuerza():
    return Nodo("_fuerza", [Nodo.Eleccion([_fuerte(), _debil()])])


def _fuerte():
    return Nodo(
        "_fuerte",
        [
            Nodo.Eleccion(
                [
                    "estrecha",
                    "intensa",
                    "profunda",
                    "solida",
                    "robusta",
                    "critica",
                    "vital",
                    "necesaria",
                    "dependiente",
                    "acoplada",
                    "integrada",
                    "fusionada",
                    "inseparable",
                    "central",
                    "nuclear",
                ]
            )
        ],
    )


def _debil():
    return Nodo(
        "_debil",
        [
            Nodo.Eleccion(
                [
                    "lejana",
                    "tenue",
                    "superficial",
                    "fragil",
                    "opcional",
                    "contingente",
                    "temporal",
                    "desacoplada",
                    "independiente",
                    "modular",
                    "separable",
                    "periferica",
                    "marginal",
                    "accidental",
                    "casual",
                ]
            )
        ],
    )


def _direccion_relaciones():
    return Nodo(
        "_direccion_relaciones", [Nodo.Eleccion([_unidireccional(), _bidireccional()])]
    )


def _unidireccional():
    return Nodo(
        "_unidireccional",
        [
            Nodo.Eleccion(
                [
                    "flujo",
                    "dependencia",
                    "herencia",
                    "delegacion",
                    "llamada",
                    "envio",
                    "publicacion",
                    "notificacion",
                    "comando",
                    "control",
                    "supervision",
                    "monitoreo",
                    "alimentacion",
                    "provision",
                    "suministro",
                ]
            )
        ],
    )


def _bidireccional():
    return Nodo(
        "_bidireccional",
        [
            Nodo.Eleccion(
                [
                    "intercambio",
                    "dialogo",
                    "negociacion",
                    "retroalimentacion",
                    "sincronizacion",
                    "coordinacion",
                    "comunicacion",
                    "colaboracion",
                    "competencia",
                    "interaccion",
                    "conexion",
                    "enlace",
                    "canal",
                    "protocolo",
                    "sesion",
                ]
            )
        ],
    )


def _naturaleza():
    return Nodo("_naturaleza", [Nodo.Eleccion([_cooperativa(), _competitiva()])])


def _cooperativa():
    return Nodo(
        "_cooperativa",
        [
            Nodo.Eleccion(
                [
                    "alianza",
                    "colaboracion",
                    "sinergia",
                    "mutualismo",
                    "solidaridad",
                    "equipo",
                    "red",
                    "comunidad",
                    "ecosistema",
                    "simbiosis",
                    "complementariedad",
                    "integracion",
                    "fusion",
                    "coordinacion",
                    "armonia",
                ]
            )
        ],
    )


def _competitiva():
    return Nodo(
        "_competitiva",
        [
            Nodo.Eleccion(
                [
                    "rivalidad",
                    "competencia",
                    "conflicto",
                    "disputa",
                    "lucha",
                    "dominacion",
                    "exclusion",
                    "monopolio",
                    "zero_sum",
                    "guerra",
                    "predacion",
                    "parasitismo",
                    "explotacion",
                    "sabotaje",
                    "traicion",
                ]
            )
        ],
    )


def _ciclos():
    return Nodo(
        "_ciclos",
        [
            Nodo.Eleccion(
                [_fases_ciclos(), _periodicidad(), _escala_ciclos(), _estado()]
            )
        ],
    )


def _fases_ciclos():
    return Nodo(
        "_fases_ciclos", [Nodo.Eleccion([_inicio_fases_ciclos(), _desarrollo()])]
    )


def _inicio_fases_ciclos():
    return Nodo(
        "_fases_ciclos",
        [
            Nodo.Eleccion(
                [
                    "nacimiento",
                    "creacion",
                    "inicializacion",
                    "activacion",
                    "lanzamiento",
                    "arranque",
                    "comienzo",
                    "genesis",
                    "origen",
                    "fundacion",
                    "instanciacion",
                    "construccion",
                    "configuracion",
                    "preparacion",
                    "calibracion",
                ]
            )
        ],
    )


def _desarrollo():
    return Nodo(
        "_fases_ciclos",
        [
            Nodo.Eleccion(
                [
                    "crecimiento",
                    "expansion",
                    "maduracion",
                    "optimizacion",
                    "especializacion",
                    "consolidacion",
                    "estabilizacion",
                    "refinamiento",
                    "aprendizaje",
                    "adaptacion",
                    "evolucion",
                    "mejora",
                    "escalado",
                    "profundizacion",
                    "diversificacion",
                ]
            )
        ],
    )


def _periodicidad():
    return Nodo("_periodicidad", [Nodo.Eleccion([_regular(), _irregular()])])


def _regular():
    return Nodo(
        "_regular",
        [
            Nodo.Eleccion(
                [
                    "constante",
                    "periodico",
                    "ciclico",
                    "ritmico",
                    "sincronizado",
                    "predecible",
                    "estable",
                    "uniforme",
                    "sistematico",
                    "repetitivo",
                    "rutinario",
                    "programado",
                    "planificado",
                    "determinista",
                    "metronomico",
                ]
            )
        ],
    )


def _irregular():
    return Nodo(
        "_irregular",
        [
            Nodo.Eleccion(
                [
                    "variable",
                    "aperiodico",
                    "estocastico",
                    "aleatorio",
                    "impredecible",
                    "inestable",
                    "caotico",
                    "turbulento",
                    "espontaneo",
                    "reactivo",
                    "adaptativo",
                    "emergente",
                    "contingente",
                    "situacional",
                    "contextual",
                ]
            )
        ],
    )


def _escala_ciclos():
    return Nodo("_escala_ciclos", [Nodo.Eleccion([_corto(), _largo()])])


def _corto():
    return Nodo(
        "_corto",
        [
            Nodo.Eleccion(
                [
                    "inmediato",
                    "rapido",
                    "micro",
                    "local",
                    "tactico",
                    "operacional",
                    "reactivo",
                    "instantaneo",
                    "temporal",
                    "transitorio",
                    "efimero",
                    "momentaneo",
                    "puntual",
                    "urgente",
                    "critico",
                ]
            )
        ],
    )


def _largo():
    return Nodo(
        "_largo",
        [
            Nodo.Eleccion(
                [
                    "prolongado",
                    "lento",
                    "macro",
                    "global",
                    "estrategico",
                    "evolutivo",
                    "historico",
                    "generacional",
                    "estructural",
                    "sistemico",
                    "profundo",
                    "fundamental",
                    "transformador",
                    "permanente",
                    "duradero",
                ]
            )
        ],
    )


def _estado():
    return Nodo("estado", [Nodo.Eleccion([_activo_estado(), _inactivo])])


def _activo_estado():
    return Nodo(
        "_activo_estado",
        [
            Nodo.Eleccion(
                [
                    "ejecutando",
                    "procesando",
                    "iterando",
                    "avanzando",
                    "creciendo",
                    "evolucionando",
                    "aprendiendo",
                    "adaptando",
                    "optimizando",
                    "explorando",
                    "explotando",
                    "comunicando",
                    "cooperando",
                    "compitiendo",
                    "sobreviviendo",
                ]
            )
        ],
    )


def _inactivo():
    return Nodo(
        "_inactivo",
        [
            Nodo.Eleccion(
                [
                    "dormido",
                    "pausado",
                    "bloqueado",
                    "esperando",
                    "suspendido",
                    "detenido",
                    "terminado",
                    "agotado",
                    "saturado",
                    "estancado",
                    "convergido",
                    "estabilizado",
                    "extinto",
                    "archivado",
                    "completado",
                ]
            )
        ],
    )


def _limites():
    return Nodo(
        "_limites",
        [
            Nodo.Eleccion(
                [_tipos_limites(), _estado_limites(), _respuesta(), _gestion_limites()]
            )
        ],
    )


def _tipos_limites():
    return Nodo(
        "_tipos_limites", [Nodo.Eleccion([_fisicos_tipos_limites(), _logicos()])]
    )


def _fisicos_tipos_limites():
    return Nodo(
        "_fisicos_tipos_limites",
        [
            Nodo.Eleccion(
                [
                    "pared",
                    "barrera",
                    "frontera",
                    "borde",
                    "superficie",
                    "membrana",
                    "interfaz",
                    "umbral",
                    "limite",
                    "capacidad",
                    "maximo",
                    "minimo",
                    "rango",
                    "dominio",
                    "alcance",
                ]
            )
        ],
    )


def _logicos():
    return Nodo(
        "_logicos",
        [
            Nodo.Eleccion(
                [
                    "restriccion",
                    "regla",
                    "condicion",
                    "invariante",
                    "precondicion",
                    "postcondicion",
                    "contrato",
                    "especificacion",
                    "requisito",
                    "permiso",
                    "prohibicion",
                    "validacion",
                    "verificacion",
                    "assertion",
                    "guardia",
                ]
            )
        ],
    )


def _estado_limites():
    return Nodo("_estado_limites", [Nodo.Eleccion([_alcanzado(), _superado()])])


def _alcanzado():
    return Nodo(
        "_alcanzado",
        [
            Nodo.Eleccion(
                [
                    "lleno",
                    "saturado",
                    "maximo",
                    "minimo",
                    "agotado",
                    "completo",
                    "terminado",
                    "bloqueado",
                    "detenido",
                    "estancado",
                    "convergido",
                    "estabilizado",
                    "optimo",
                    "critico",
                    "umbral",
                ]
            )
        ],
    )


def _superado():
    return Nodo(
        "_superado",
        [
            Nodo.Eleccion(
                [
                    "desbordado",
                    "excedido",
                    "violado",
                    "roto",
                    "sobrepasado",
                    "transgredido",
                    "ignorado",
                    "bypass",
                    "workaround",
                    "hack",
                    "exploit",
                    "overflow",
                    "underflow",
                    "wrap",
                    "truncado",
                ]
            )
        ],
    )


def _respuesta():
    return Nodo("_respuesta", [Nodo.Eleccion([_bloqueo(), _desbordamiento()])])


def _bloqueo():
    return Nodo(
        "_bloqueo",
        [
            Nodo.Eleccion(
                [
                    "parada",
                    "espera",
                    "suspension",
                    "rechazo",
                    "error",
                    "excepcion",
                    "timeout",
                    "deadlock",
                    "livelock",
                    "starvation",
                    "throttling",
                    "rate_limit",
                    "circuit_breaker",
                    "backpressure",
                    "shed_load",
                ]
            )
        ],
    )


def _desbordamiento():
    return Nodo(
        "_desbordamiento",
        [
            Nodo.Eleccion(
                [
                    "overflow",
                    "wrap",
                    "truncado",
                    "perdida",
                    "descarte",
                    "degradacion",
                    "fallback",
                    "graceful",
                    "recovery",
                    "reinicio",
                    "reset",
                    "rollback",
                    "compensacion",
                    "mitigacion",
                    "adaptacion",
                ]
            )
        ],
    )


def _gestion_limites():
    return Nodo(
        "_gestion_limites",
        [Nodo.Eleccion([_control_gestion_limites(), _adaptacion_gestion_limites()])],
    )


def _control_gestion_limites():
    return Nodo(
        "_control_gestion_limites",
        [
            Nodo.Eleccion(
                [
                    "monitoreo",
                    "supervision",
                    "enforcement",
                    "validacion",
                    "verificacion",
                    "auditoria",
                    "trazabilidad",
                    "logging",
                    "alertas",
                    "umbrales",
                    "politicas",
                    "reglas",
                    "contratos",
                    "invariantes",
                    "assertions",
                ]
            )
        ],
    )


def _adaptacion_gestion_limites():
    return Nodo(
        "_adaptacion_gestion_limites",
        [
            Nodo.Eleccion(
                [
                    "ajuste",
                    "flexibilizacion",
                    "renegociacion",
                    "extension",
                    "compresion",
                    "escalado",
                    "dinamico",
                    "elastico",
                    "adaptativo",
                    "reactivo",
                    "proactivo",
                    "predictivo",
                    "aprendizaje",
                    "evolucion",
                    "optimizacion",
                ]
            )
        ],
    )


def _cambio():
    return Nodo(
        "_cambio",
        [
            Nodo.Eleccion(
                [_tipo_cambio(), _direccion_cambio(), _causa_cambio(), _efecto_cambio()]
            )
        ],
    )


def _tipo_cambio():
    return Nodo("_tipo_cambio", [Nodo.Eleccion([_gradual(), _abrupto()])])


def _gradual():
    return Nodo(
        "_gradual",
        [
            Nodo.Eleccion(
                [
                    "incremental",
                    "continuo",
                    "suave",
                    "lento",
                    "progresivo",
                    "acumulativo",
                    "evolutivo",
                    "refinamiento",
                    "optimizacion",
                    "convergencia",
                    "aprendizaje",
                    "adaptacion",
                    "maduracion",
                    "especializacion",
                    "consolidacion",
                ]
            )
        ],
    )


def _abrupto():
    return Nodo(
        "_abrupto",
        [
            Nodo.Eleccion(
                [
                    "discontinuo",
                    "brusco",
                    "rapido",
                    "salto",
                    "ruptura",
                    "transicion",
                    "fase",
                    "critico",
                    "umbral",
                    "tipping_point",
                    "cascada",
                    "colapso",
                    "emergencia",
                    "revolucion",
                    "transformacion",
                ]
            )
        ],
    )


def _direccion_cambio():
    return Nodo(
        "_direccion_cambio",
        [Nodo.Eleccion([_aumento_direccion_cambio(), _disminucion_direccion_cambio()])],
    )


def _aumento_direccion_cambio():
    return Nodo(
        "_aumento_direccion_cambio",
        [
            Nodo.Eleccion(
                [
                    "crecimiento",
                    "expansion",
                    "amplificacion",
                    "aceleracion",
                    "intensificacion",
                    "escalado",
                    "proliferacion",
                    "multiplicacion",
                    "refuerzo",
                    "potenciacion",
                    "maximizacion",
                    "optimizacion",
                    "mejora",
                    "avance",
                    "progreso",
                ]
            )
        ],
    )


def _disminucion_direccion_cambio():
    return Nodo(
        "_disminucion_direccion_cambio",
        [
            Nodo.Eleccion(
                [
                    "reduccion",
                    "contraccion",
                    "atenuacion",
                    "desaceleracion",
                    "simplificacion",
                    "minimizacion",
                    "poda",
                    "eliminacion",
                    "degradacion",
                    "deterioro",
                    "perdida",
                    "extincion",
                    "colapso",
                    "convergencia",
                    "especializacion",
                ]
            )
        ],
    )


def _causa_cambio():
    return Nodo("_causa_cambio", [Nodo.Eleccion([_interno(), _externo()])])


def _interno():
    return Nodo(
        "_interno",
        [
            Nodo.Eleccion(
                [
                    "mutacion",
                    "aprendizaje",
                    "adaptacion",
                    "optimizacion",
                    "evolucion",
                    "maduracion",
                    "crecimiento",
                    "degradacion",
                    "agotamiento",
                    "saturacion",
                    "fallo",
                    "error",
                    "innovacion",
                    "creatividad",
                    "reorganizacion",
                ]
            )
        ],
    )


def _externo():
    return Nodo(
        "_externo",
        [
            Nodo.Eleccion(
                [
                    "presion",
                    "perturbacion",
                    "estimulo",
                    "señal",
                    "evento",
                    "colision",
                    "interaccion",
                    "competencia",
                    "cooperacion",
                    "ambiente",
                    "recurso",
                    "restriccion",
                    "oportunidad",
                    "amenaza",
                    "cambio_contexto",
                ]
            )
        ],
    )


def _efecto_cambio():
    return Nodo("_efecto_cambio", [Nodo.Eleccion([_local(), _global()])])


def _local():
    return Nodo(
        "_local",
        [
            Nodo.Eleccion(
                [
                    "puntual",
                    "inmediato",
                    "directo",
                    "especifico",
                    "concreto",
                    "observable",
                    "medible",
                    "controlable",
                    "reversible",
                    "trazable",
                    "aislado",
                    "contenido",
                    "limitado",
                    "parcial",
                    "temporal",
                ]
            )
        ],
    )


def _global():
    return Nodo(
        "_global",
        [
            Nodo.Eleccion(
                [
                    "sistemico",
                    "indirecto",
                    "difuso",
                    "emergente",
                    "acumulado",
                    "cascada",
                    "no_lineal",
                    "impredecible",
                    "irreversible",
                    "permanente",
                    "estructural",
                    "transformador",
                    "evolutivo",
                    "historico",
                    "fundamental",
                ]
            )
        ],
    )


def _estructura():
    return Nodo(
        "_estructura",
        [
            Nodo.Eleccion(
                [
                    _organizacion_estructura(),
                    _conexiones(),
                    _rigidez(),
                    _escala_estructura(),
                ]
            )
        ],
    )


def _organizacion_estructura():
    return Nodo("_organizacion_estructura", [Nodo.Eleccion([_jerarquica(), _plana()])])


def _jerarquica():
    return Nodo(
        "_jerarquica",
        [
            Nodo.Eleccion(
                [
                    "arbol",
                    "padre",
                    "hijo",
                    "nivel",
                    "profundidad",
                    "raiz",
                    "hoja",
                    "rama",
                    "subárbol",
                    "ancestro",
                    "descendiente",
                    "rango",
                    "orden",
                    "cadena",
                    "escalon",
                ]
            )
        ],
    )


def _plana():
    return Nodo(
        "_plana",
        [
            Nodo.Eleccion(
                [
                    "red",
                    "grafo",
                    "par",
                    "igual",
                    "horizontal",
                    "distribuido",
                    "descentralizado",
                    "autonomo",
                    "independiente",
                    "modular",
                    "loosely_coupled",
                    "microservicio",
                    "peer",
                    "mesh",
                    "swarm",
                ]
            )
        ],
    )


def _conexiones():
    return Nodo("_conexiones", [Nodo.Eleccion([_densas(), _dispersas()])])


def _densas():
    return Nodo(
        "_densas",
        [
            Nodo.Eleccion(
                [
                    "acoplado",
                    "integrado",
                    "dependiente",
                    "cohesivo",
                    "monolitico",
                    "centralizado",
                    "sincronizado",
                    "coordinado",
                    "orquestado",
                    "controlado",
                    "dirigido",
                    "planificado",
                    "rigido",
                    "estrecho",
                    "fuerte",
                ]
            )
        ],
    )


def _dispersas():
    return Nodo(
        "_dispersas",
        [
            Nodo.Eleccion(
                [
                    "desacoplado",
                    "independiente",
                    "autonomo",
                    "modular",
                    "distribuido",
                    "eventual",
                    "asincrono",
                    "reactivo",
                    "emergente",
                    "flexible",
                    "adaptativo",
                    "resiliente",
                    "tolerante",
                    "loose",
                    "debil",
                ]
            )
        ],
    )


def _rigidez():
    return Nodo("_rigidez", [Nodo.Eleccion([_fija(), _flexible()])])


def _fija():
    return Nodo(
        "_fija",
        [
            Nodo.Eleccion(
                [
                    "estatica",
                    "rigida",
                    "inmutable",
                    "determinista",
                    "predecible",
                    "estable",
                    "consistente",
                    "uniforme",
                    "estandarizada",
                    "normalizada",
                    "formalizada",
                    "especificada",
                    "contratada",
                    "garantizada",
                    "certificada",
                ]
            )
        ],
    )


def _flexible():
    return Nodo(
        "_flexible",
        [
            Nodo.Eleccion(
                [
                    "dinamica",
                    "adaptativa",
                    "mutable",
                    "estocastica",
                    "impredecible",
                    "variable",
                    "inconsistente",
                    "heterogenea",
                    "personalizada",
                    "contextual",
                    "situacional",
                    "emergente",
                    "evolutiva",
                    "plastica",
                    "maleable",
                ]
            )
        ],
    )


def _escala_estructura():
    return Nodo("_escala_estructura", [Nodo.Eleccion([_simple(), _compleja()])])


def _simple():
    return Nodo(
        "_simple",
        [
            Nodo.Eleccion(
                [
                    "pequeno",
                    "unitario",
                    "atomico",
                    "elemental",
                    "primitivo",
                    "basico",
                    "minimo",
                    "reducido",
                    "compacto",
                    "conciso",
                    "claro",
                    "obvio",
                    "directo",
                    "lineal",
                    "trivial",
                ]
            )
        ],
    )


def _compleja():
    return Nodo(
        "_compleja",
        [
            Nodo.Eleccion(
                [
                    "grande",
                    "compuesto",
                    "molecular",
                    "sistemico",
                    "emergente",
                    "no_lineal",
                    "caotico",
                    "jerarquico",
                    "recursivo",
                    "fractal",
                    "adaptativo",
                    "evolutivo",
                    "distribuido",
                    "paralelo",
                    "concurrente",
                ]
            )
        ],
    )
#endregion

guia = {"programa": _programa()}
