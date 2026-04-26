from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.elementos import Nodo
from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.librerias import _libreria
from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.strings_pool import _stringsPool
from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.Capacidades.capacidades import (
    _capacidad,
)
from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.inyeccion import (
    _codigoInyectado,
    _importsHardCoded,
)


"""
    TODO: posible implementacion: _iterable
"""


def _programa():
    return Nodo(
        "_programa",
        [
            "#---------------------------------\n",
            _importsHardCoded,  # ----------------------    Imports que todos los bots disponen sin coste
            "\n",
            "#---------------------------------\n",
            "# Codigo Inyectado\n",
            "#---------------------------------\n",
            _codigoInyectado,  # -----------------------   Codigo inyectado a mano
            "\n",
            "#---------------------------------\n",
            "# Funciones:\n",
            "#---------------------------------\n",
            _funciones,
            "\n",
            "#---------------------------------\n",
            "# Codigo:\n",
            "#---------------------------------\n",
            _codigo,
        ],
    )


def _asignacion():
    return Nodo(
        "_asignacion",
        [
            _variable,
            " = ",
            Nodo.Eleccion(
                [
                    _dato,
                    _operacion,
                ]
            ),
            "\n",
        ],
    )


def _controlAsincrono():
    return Nodo(
        "_controlAsincrono",
        [
            Nodo.Eleccion(
                [
                    _bucleAsincrono,
                    _condicional,
                    _control,
                    _controlEstructural,
                    _declaracionEstructural,
                    _withAsincrono,
                ]
            )
        ],
    )


def _codigoBucleAsincrono():
    return Nodo(
        "_codigoBucleAsincrono",
        [
            Nodo.Eleccion(
                [
                    _operacion,
                    _asignacion,
                    _controlAsincrono,
                    _ejecucion,
                    _comentario,
                    _return,
                    _await,
                    _break,
                    _continue,
                ]
            ),
            Nodo.Eleccion([_codigoBucleAsincrono, _stop]),
        ],
    )


def _whileAsincrono():
    return Nodo(
        "_whileAsincrono",
        [
            "while ",
            _condicion,
            ":",
            "\n",
            Nodo.Tab(_codigoBucleAsincrono),
            "\n",
            Nodo.Eleccion([["\n", _else], _stop]),
            "\n",
        ],
    )


def _bucleAsincrono():
    return Nodo(
        "_bucleAsincrono",
        [
            Nodo.Eleccion(
                [
                    _forAsincrono,
                    _whileAsincrono,
                ]
            )
        ],
    )


def _forAsincrono():
    return Nodo(
        "_forAsincrono",
        [
            "async for ",
            _variable,
            " in ",
            Nodo.Eleccion(
                [
                    _variable,
                    _llamadaFuncion,
                ]
            ),
            ":\n",
            Nodo.Tab(_codigoBucleAsincrono),
            "\n",
        ],
    )


def _withAsincrono():
    return Nodo(
        "_withAsincrono",
        [
            "async with ",
            _llamadaFuncion,
            " as ",
            _variable,
            ":\n",
            Nodo.Tab(_codigoFuncionAsincrona),
            "\n",
        ],
    )


def _control():
    return Nodo(
        "_control",
        [
            Nodo.Eleccion(
                [
                    _bucle,
                    _condicional,
                    _controlEstructural,
                    _declaracionEstructural,
                ]
            )
        ],
    )


def _bucle():
    return Nodo("_bucle", [Nodo.Eleccion([_for, _while])])


def _for():
    return Nodo(
        "_for", [Nodo.Eleccion([_forLista, _forIndice, _forNumerico, _forDict])]
    )


def _condicional():
    return Nodo("_condicional", [Nodo.Eleccion([_if, _match])])


def _if():
    return Nodo(
        "_if",
        [
            "if ",
            _condicion,
            ":\n",
            Nodo.Tab(_codigo),
            "\n",
            Nodo.Eleccion([[Nodo.Eleccion([_else, _elif])], _stop]),
        ],
    )


def _elif():
    return Nodo(
        "_elif",
        [
            "elif ",
            _condicion,
            ":\n",
            Nodo.Tab(_codigo),
            "\n",
            Nodo.Eleccion([Nodo.Eleccion([_else, _elif]), _stop]),
            "\n",
        ],
    )


def _else():
    return Nodo("_else", ["else:\n", Nodo.Tab(_codigo), "\n"])


def _condicion():
    return Nodo(
        "_condicion",
        [
            Nodo.Eleccion(
                [
                    _comparacion,
                    _comparacionMembership,
                    _comparacionIdentidad,
                    _operacionLogica,
                    _bool,
                    _none,
                    _variable,
                    _llamadaFuncion,
                ]
            )
        ],
    )


def _comparacionMembership():
    return Nodo(
        "_comparacionMembership",
        [
            _dato,
            Nodo.Eleccion([" in ", " not in "]),
            _dato,
        ],
    )


def _comparacionIdentidad():
    return Nodo(
        "_comparacionIdentidad",
        [
            _dato,
            Nodo.Eleccion([" is ", " is not "]),
            _dato,
        ],
    )


def _return():
    return Nodo(
        "_return",
        [
            "return ",
            Nodo.Eleccion(
                [
                    [
                        Nodo.Eleccion(
                            [
                                _dato,
                                _llamadaFuncion,
                            ]
                        ),
                    ],
                    _stop,
                ]
            ),
            "\n",
        ],
    )


def _yield():
    return Nodo(
        "_yield", ["yield ", " ", Nodo.Eleccion([_dato, _llamadaFuncion]), "\n"]
    )


def _await():
    return Nodo(
        "_await",
        [
            "await ",
            Nodo.Eleccion(
                [
                    _llamadaFuncion,
                    _variable,
                ]
            ),
            "\n",
        ],
    )


def _controlEstructural():
    return Nodo(
        "_controlEstructural",
        [
            Nodo.Eleccion(
                [
                    _try,
                    _with,
                ]
            )
        ],
    )


def _try():
    return Nodo(
        "_try",
        [
            "try:",
            "\n",
            Nodo.Tab(_codigo),
            "\n",
            "except",
            Nodo.Eleccion([[" ", _palabra], _stop]),
            ":",
            "\n",
            Nodo.Tab(_codigo),
            "\n",
            Nodo.Eleccion(
                [
                    Nodo.Eleccion(
                        [
                            _else,
                            _finally,
                            [
                                _else,
                                _finally,
                            ],
                        ]
                    ),
                    _stop,
                ]
            ),
        ],
    )


def _finally():
    return Nodo("_finally", ["finally:\n", Nodo.Tab(_codigo), "\n"])


def _with():
    return Nodo(
        "_with",
        [
            "with ",
            Nodo.Eleccion(
                [
                    _llamadaFuncion,
                    _variable,
                    _invocarMetodo,
                ]
            ),
            Nodo.Eleccion([[" as ", _variable], _stop]),
            ":\n",
            Nodo.Tab(_codigoFuncion),
            "\n",
        ],
    )


def _declaracionEstructural():
    return Nodo(
        "_declaracionEstructural",
        [
            Nodo.Eleccion(
                [
                    _llamadaFuncion,
                    _clase,
                ]
            )
        ],
    )


def _argumentos():
    return Nodo(
        "_argumentos",
        [
            _argumento,
            Nodo.Eleccion(
                [
                    [
                        ", ",
                        _argumentos,
                    ],
                    _stop,
                ]
            ),
        ],
    )


def _argumento():
    return Nodo(
        "_argumento",
        [
            Nodo.Eleccion(
                [
                    [_variable, "=", _dato],
                    _dato,
                ]
            )
        ],
    )


def _parametros():
    return Nodo(
        "_parametros",
        [
            _parametro,
            Nodo.Eleccion([[", ", _parametros], _stop]),
        ],
    )


def _parametro():
    return Nodo(
        "_parametro",
        [
            Nodo.Eleccion(
                [
                    _parametroNormal,
                    _parametroDefault,
                    _parametroAnotado,
                    _parametroAnotadoDefault,
                    _parametroArgs,
                    _parametroKwargs,
                ]
            )
        ],
    )


def _parametroNormal():
    return Nodo("_parametroNormal", [_variable])


def _parametroDefault():
    return Nodo("_parametroDefault", [_variable, "=", _dato])


def _parametroAnotado():
    return Nodo("_parametroAnotado", [_variable, ": ", _builtinTipos])


def _parametroAnotadoDefault():
    return Nodo(
        "_parametroAnotadoDefault", [_variable, ": ", _builtinTipos, " = ", _dato]
    )


def _parametroArgs():
    return Nodo("_parametroArgs", ["*", _variable])


def _parametroKwargs():
    return Nodo("_parametroKwargs", ["**", _variable])


def _variablesClase():
    return Nodo(
        "_variablesClase",
        [
            _variable,
            Nodo.Eleccion(
                [
                    [", ", _variablesClase],
                    _stop,
                ],
            ),
        ],
    )


def _funcionesClase():
    return Nodo(
        "_funcionesClase",
        [
            _funcionClase,
            "\n",
            Nodo.Eleccion([_funcionesClase, _stop]),
        ],
    )


def _metodoEspecial():
    return Nodo(
        "_metodoEspecial",
        [
            Nodo.Eleccion(
                [
                    _metodoEspecialSelf,
                    _metodoEspecialSelfOther,
                    _metodoEspecialSelfKey,
                    _metodoEspecialSelfKeyValue,
                    _metodoEspecialCall,
                    _metodoEspecialExit,
                    _metodoEspecialEnter,
                ]
            )
        ],
    )


def _metodoEspecialSelf():
    return Nodo(
        "_metodoEspecialSelf",
        [
            "def ",
            Nodo.Eleccion(
                [
                    "__str__",
                    "__repr__",
                    "__len__",
                    "__iter__",
                    "__next__",
                    "__hash__",
                    "__bool__",
                ]
            ),
            "(self):",
            "\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _metodoEspecialSelfOther():
    return Nodo(
        "_metodoEspecialSelfOther",
        [
            "def ",
            Nodo.Eleccion(
                [
                    "__eq__",
                    "__ne__",
                    "__lt__",
                    "__gt__",
                    "__le__",
                    "__ge__",
                    "__add__",
                    "__sub__",
                    "__mul__",
                    "__truediv__",
                    "__mod__",
                    "__pow__",
                ]
            ),
            "(self, other):",
            "\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _metodoEspecialSelfKey():
    return Nodo(
        "_metodoEspecialSelfKey",
        [
            "def ",
            Nodo.Eleccion(
                [
                    "__getitem__",
                    "__delitem__",
                    "__contains__",
                ]
            ),
            "(self, key):",
            "\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _metodoEspecialSelfKeyValue():
    return Nodo(
        "_metodoEspecialSelfKeyValue",
        [
            "def __setitem__(self, key, value):",
            "\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _metodoEspecialCall():
    return Nodo(
        "_metodoEspecialCall",
        [
            "def __call__(self, *args, **kwargs):",
            "\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _metodoEspecialEnter():
    return Nodo(
        "_metodoEspecialEnter",
        [
            "def __enter__(self):",
            "\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _metodoEspecialExit():
    return Nodo(
        "_metodoEspecialExit",
        [
            "def __exit__(self, exc_type, exc_val, exc_tb):",
            "\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _funcionClase():
    return Nodo(
        "_funcionClase",
        [
            Nodo.Eleccion(
                [
                    _declaracionMetodo,
                    _metodoEspecial,
                ]
            )
        ],
    )


def _operacion():
    return Nodo(
        "_operacion",
        [Nodo.Eleccion([_operacionAritmetica, _operacionLogica, _operacionBitwise])],
    )


def _operacionAritmetica():
    return Nodo(
        "_operacionAritmetica",
        [
            Nodo.Eleccion(
                [
                    _suma,
                    _resta,
                    _multiplicacion,
                    _division,
                    _modulo,
                    _potencia,
                    _raiz,
                ]
            )
        ],
    )


def _suma():
    return Nodo(
        "_suma",
        [
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
            " ",
            _simboloSuma,
            " ",
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
        ],
    )


def _resta():
    return Nodo(
        "_resta",
        [
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
            " ",
            _simboloResta,
            " ",
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
        ],
    )


def _multiplicacion():
    return Nodo(
        "_multiplicacion",
        [
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
            " ",
            _simboloMultiplicacion,
            " ",
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
        ],
    )


def _division():
    return Nodo(
        "_division",
        [
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
            " ",
            _simboloDivision,
            " ",
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
        ],
    )


def _modulo():
    return Nodo(
        "_modulo",
        [
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
            " ",
            _simboloModulo,
            " ",
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
        ],
    )


def _potencia():
    return Nodo(
        "_potencia",
        [
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
            " ",
            _simboloPotencia,
            " ",
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
        ],
    )


def _raiz():
    return Nodo(
        "_raiz",
        [
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
            " ** (1 / ",
            Nodo.Eleccion([_variable, _numero, _llamadaFuncion, _operacion]),
            ")",
        ],
    )


def _comparacion():
    return Nodo("_comparacion", [_dato, " ", _simboloComparacion, " ", _dato])


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
                    _mascaraAnd,
                    _mascaraOr,
                    _mascaraNot,
                    _mascaraShiftIzquierda,
                    _mascaraShiftDerecha,
                ]
            )
        ],
    )


def _mascaraAnd():
    return Nodo("_mascaraAnd", [_dato, " & ", _dato])


def _mascaraOr():
    return Nodo("_mascaraOr", [_dato, " | ", _dato])


def _mascaraNot():
    return Nodo("_mascaraNot", ["~", _dato])


def _comentario():
    return Nodo("_comentario", [Nodo.Eleccion([_comentarioLinea, _comentarioBloque])])


def _comentarioLinea():
    return Nodo("_comentarioLinea", ["# ", _contenidoComentario, "\n"])


def _comentarioBloque():
    return Nodo("_comentarioBloque", ["'''", "\n", _contenidoComentario, "\n", "'''"])


def _contenidoComentario():
    return Nodo(
        "_contenidoComentario",
        [
            Nodo.Eleccion([_stringsPool, _texto]),
            Nodo.Eleccion([_contenidoComentario, _stop]),
        ],
    )


def _textoLetrasSimbolos():
    return Nodo(
        "_textoLetrasSimbolos",
        [
            Nodo.Eleccion([_letra, _simbolo]),
            Nodo.Eleccion([_textoLetrasSimbolos, _stop]),
        ],
    )


def _textoLetrasNumeros():
    return Nodo(
        "_textoLetrasNumeros",
        [
            Nodo.Eleccion([_letra, _digito]),
            Nodo.Eleccion([_textoLetrasNumeros, _stop]),
        ],
    )


def _textoLetras():
    return Nodo("_textoLetras", [_letra, Nodo.Eleccion([_textoLetras, _stop])])


def _texto():
    return Nodo(
        "_texto",
        [
            Nodo.Eleccion(
                [
                    _textoLetras,
                    _textoLetrasNumeros,
                    _textoLetrasSimbolos,
                ]
            )
        ],
    )


def _variable():
    return Nodo("_variable", [_letra, _textoLetrasNumeros])


def _funciones():
    return Nodo(
        "_funciones", [_funcion, "\n", Nodo.Eleccion([_funciones, _stop]), "\n"]
    )


def _codigo():
    return Nodo(
        "_codigo",
        [
            Nodo.Eleccion(
                [
                    _operacion,
                    _asignacion,
                    _ejecucion,
                    _control,
                    _funcion,
                    _clase,
                    _raise,
                    _comentario,
                    _libreria,
                    _capacidad,
                ]
            ),
            Nodo.Eleccion([_codigo, _stop]),
        ],
    )


def _codigoFuncion():
    return Nodo(
        "_codigoFuncion",
        [
            Nodo.Eleccion(
                [
                    _operacion,
                    _asignacion,
                    _control,
                    _ejecucion,
                    _comentario,
                    _return,
                    _yield,
                    _raise,
                    _clase,
                ]
            ),
            Nodo.Eleccion([_codigoFuncion, _stop]),
        ],
    )


def _codigoBucle():
    return Nodo(
        "_codigoBucle",
        [
            Nodo.Eleccion(
                [
                    _operacion,
                    _asignacion,
                    _control,
                    _ejecucion,
                    _comentario,
                    _return,
                    _break,
                    _continue,
                    _raise,
                ]
            ),
            Nodo.Eleccion([_codigoBucle, _stop]),
        ],
    )


def _codigoFuncionAsincrona():
    return Nodo(
        "_codigoFuncionAsincrona",
        [
            Nodo.Eleccion(
                [
                    _operacion,
                    _asignacion,
                    _controlAsincrono,
                    _ejecucion,
                    _comentario,
                    _return,
                    _yield,
                    _await,
                    _raise,
                ]
            ),
            Nodo.Eleccion([_codigoFuncionAsincrona, _stop]),
        ],
    )


def _codigoGenerador():
    return Nodo(
        "_codigoGenerador",
        [
            Nodo.Eleccion(
                [
                    _operacion,
                    _asignacion,
                    _control,
                    _ejecucion,
                    _comentario,
                    _yield,
                    _return,
                    _raise,
                ]
            ),
            Nodo.Eleccion([_codigoGenerador, _stop]),
        ],
    )


def _conjunto():
    return Nodo(
        "_conjunto",
        [
            Nodo.Eleccion(
                [
                    _lista,
                    _tupla,
                    _diccionario,
                    _set,
                    _comprehension,
                ]
            )
        ],
    )


def _set():
    return Nodo("_set", ["{", _argumentos, "}"])


def _diccionario():
    return Nodo("_diccionario", ["{", _argumentosKV, "}"])


def _argumentosKV():
    return Nodo(
        "_argumentosKV",
        [_argumentoKV, Nodo.Eleccion([[", ", _argumentosKV], _stop])],
    )


def _argumentoKV():
    return Nodo("_argumentoKV", [_string, ": ", Nodo.Eleccion([_dato, _funcion])])


def _tupla():
    return Nodo("_tupla", ["(", _argumentos, ")"])


def _lista():
    return Nodo("_lista", ["[", _argumentos, "]"])


def _bool():
    return Nodo("_bool", [Nodo.Eleccion([_true, _false])])


def _string():
    return Nodo(
        "_string",
        [
            Nodo.Eleccion(
                [
                    _stringNormal,
                    _stringF,
                    _byteString,
                    _rawString,
                ]
            )
        ],
    )


def _stringNormal():
    return Nodo(
        "_stringNormal",
        [
            '"',
            _palabra,
            '"',
        ],
    )


def _stringF():
    return Nodo(
        "_stringF",
        [
            'f"',
            _textoLetras,
            Nodo.Eleccion(
                [
                    ["{", _expresionSimple, "}", _textoLetras],
                    _stop,
                ]
            ),
            '"',
        ],
    )


def _byteString():
    return Nodo("_byteString", ['b"', _palabra, '"'])


def _rawString():
    return Nodo("_rawString", ['r"', _palabra, '"'])


def _palabra():
    return Nodo("_palabra", [_char, Nodo.Eleccion([_palabra, _stop])])


def _char():
    return Nodo("_char", [Nodo.Eleccion([_letra, _simbolo])])


def _letra():
    return Nodo("_letra", [Nodo.Eleccion([_minuscula, _mayuscula])])


def _minuscula():
    return Nodo(
        "_minuscula",
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
                ]
            )
        ],
    )


def _mayuscula():
    return Nodo(
        "_mayuscula",
        [
            Nodo.Eleccion(
                [
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
                    _simboloAritmetico,
                    _simboloLogico,
                    _simboloComparacion,
                    _parentesis,
                    _corchetes,
                    _llaves,
                    _comillas,
                    _simboloTexto,
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
                    _simboloSuma,
                    _simboloResta,
                    _simboloMultiplicacion,
                    _simboloDivision,
                    _simboloModulo,
                    _simboloPotencia,
                ]
            )
        ],
    )


def _simboloLogico():
    return Nodo("_simboloLogico", [Nodo.Eleccion([_and, _or, _not])])


def _and():
    return Nodo("_and", ["and"])


def _or():
    return Nodo("_or", ["or"])


def _not():
    return Nodo("_not", ["not"])


def _simboloComparacion():
    return Nodo(
        "_simboloComparacion",
        [
            Nodo.Eleccion(
                [
                    _equal,
                    _notEqual,
                    _greaterThan,
                    _lowerThan,
                    _greaterOrEqualThan,
                    _lowerOrEqualThan,
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
            Nodo.Eleccion(
                [
                    Nodo.Eleccion(
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
                        ]
                    ),
                    Nodo.Eleccion(
                        [
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
                        ]
                    ),
                ]
            )
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
        "_numero",
        [
            Nodo.Eleccion([_positivo, _negativo]),
            Nodo.Eleccion([_integer, _double, _complex]),
        ],
    )


def _integer():
    return Nodo("_integer", [_digito, Nodo.Eleccion([_integer, _stop])])


def _double():
    return Nodo("_double", [_integer, ".", _integer])


def _complex():
    return Nodo(
        "_complex",
        [
            "complex(",
            Nodo.Eleccion([_positivo, _negativo]),
            Nodo.Eleccion([_integer, _double]),
            ", ",
            Nodo.Eleccion([_positivo, _negativo]),
            Nodo.Eleccion([_integer, _double]),
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
                    _numero,
                    _string,
                    _bool,
                    _none,
                    _conjunto,
                    _elipsis,
                    _variable,
                    _declaracionFuncionLambda,
                    _leerAtributoClase,
                    _llamadaFuncion,
                    _invocarMetodo,
                    _expresionTernaria,
                    _comprehension,
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
                    _operacionAnd,
                    _operacionOr,
                    _operacionNot,
                    _comparacion,
                    _true,
                    _false,
                ]
            )
        ],
    )


def _operacionAnd():
    return Nodo("_operacionAnd", ["(", _condicion, " ", _and, " ", _condicion, ")"])


def _operacionOr():
    return Nodo("_operacionOr", ["(", _condicion, " ", _or, " ", _condicion, ")"])


def _operacionNot():
    return Nodo("_operacionNot", [_not, "(", _condicion, ")"])


def _mascaraShiftIzquierda():
    return Nodo("_mascaraShiftIzquierda", [_dato, "<<", _dato])


def _mascaraShiftDerecha():
    return Nodo("_mascaraShiftDerecha", [_dato, ">>", _dato])


def _forLista():
    return Nodo(
        "_forLista",
        [
            "for ",
            _variable,
            " in ",
            _variable,
            ":",
            "\n",
            Nodo.Tab(_codigoBucle),
            "\n",
        ],
    )


def _forIndice():
    return Nodo(
        "_forIndice",
        [
            "for ",
            _variable,
            ", ",
            _variable,
            " in enumerate(",
            _variable,
            ", start=",
            _integer,
            "):",
            "\n",
            Nodo.Tab(_codigoBucle),
            "\n",
        ],
    )


def _forNumerico():
    return Nodo(
        "_forNumerico",
        [
            "for ",
            _variable,
            " in range(",
            Nodo.Eleccion(
                [
                    [Nodo.Eleccion([_integer, _variable, _llamadaFuncion])],
                    [
                        Nodo.Eleccion([_integer, _variable, _llamadaFuncion]),
                        ", ",
                        Nodo.Eleccion([_integer, _variable, _llamadaFuncion]),
                    ],
                    [
                        Nodo.Eleccion([_integer, _variable, _llamadaFuncion]),
                        ", ",
                        Nodo.Eleccion([_integer, _variable, _llamadaFuncion]),
                        ", ",
                        Nodo.Eleccion([_integer, _variable, _llamadaFuncion]),
                    ],
                ]
            ),
            "):",
            "\n",
            Nodo.Tab(_codigoBucle),
            "\n",
        ],
    )


def _forDict():
    return Nodo(
        "_forDict",
        [
            Nodo.Eleccion(
                [
                    _forDictKeys,
                    _forDictValues,
                    _forDictItems,
                ]
            )
        ],
    )


def _forDictKeys():
    return Nodo(
        "_forDictKeys",
        [
            "for ",
            _variable,
            " in ",
            _variable,
            ".keys():",
            "\n",
            Nodo.Tab(_codigoBucle),
            "\n",
        ],
    )


def _forDictValues():
    return Nodo(
        "_forDictValues",
        [
            "for ",
            _variable,
            " in ",
            _variable,
            ".values():",
            "\n",
            Nodo.Tab(_codigoBucle),
            "\n",
        ],
    )


def _forDictItems():
    return Nodo(
        "_forDictItems",
        [
            "for ",
            _variable,
            ", ",
            _variable,
            " in ",
            _variable,
            ".items():",
            "\n",
            Nodo.Tab(_codigoBucle),
            "\n",
        ],
    )


def _comprehension():
    return Nodo(
        "_comprehension",
        [
            Nodo.Eleccion(
                [
                    _listComprehension,
                    _dictComprehension,
                    _setComprehension,
                    _generatorExpression,
                ]
            )
        ],
    )


def _listComprehension():
    return Nodo(
        "_listComprehension",
        [
            "[",
            _expresionSimple,
            " for ",
            _variable,
            " in ",
            _dato,
            Nodo.Eleccion([[" if ", _condicion], _stop]),
            "]",
        ],
    )


def _dictComprehension():
    return Nodo(
        "_dictComprehension",
        [
            "{",
            _expresionSimple,
            ": ",
            _expresionSimple,
            " for ",
            _variable,
            " in ",
            _dato,
            Nodo.Eleccion([[" if ", _condicion], _stop]),
            "}",
        ],
    )


def _setComprehension():
    return Nodo(
        "_setComprehension",
        [
            "{",
            _expresionSimple,
            " for ",
            _variable,
            " in ",
            _dato,
            Nodo.Eleccion([[" if ", _condicion], _stop]),
            "}",
        ],
    )


def _generatorExpression():
    return Nodo(
        "_generatorExpression",
        [
            "(",
            _expresionSimple,
            " for ",
            _variable,
            " in ",
            _dato,
            Nodo.Eleccion([[" if ", _condicion], _stop]),
            ")",
        ],
    )


def _break():
    return Nodo("_break", ["break ", "\n"])


def _while():
    return Nodo(
        "_while",
        [
            "while ",
            _condicion,
            ":",
            "\n",
            Nodo.Tab(_codigoBucle),
            "\n",
            Nodo.Eleccion([["\n", _else], _stop]),
            "\n",
        ],
    )


def _continue():
    return Nodo("_continue", ["continue", "\n"])


def _match():
    return Nodo(
        "_match",
        [
            "match ",
            Nodo.Eleccion([_variable, _funcion]),
            ":",
            "\n",
            _cases,
            Nodo.Eleccion([["case _:\n", _codigo], _stop]),
        ],
    )


def _cases():
    return Nodo(
        "_cases",
        [
            "case ",
            Nodo.Eleccion(
                [
                    _patron,
                    _stop,  # case _: ya está separado fuera
                ]
            ),
            ":",
            "\n",
            Nodo.Tab(_codigo),
            "\n",
            Nodo.Eleccion([_cases, _stop]),
        ],
    )


def _patron():
    return Nodo(
        "_patron",
        [
            Nodo.Eleccion(
                [
                    _numero,  # case 42:
                    _string,  # case "hola":
                    _none,  # case None:
                    _bool,  # case True:
                    _variable,  # case x: (captura)
                    _patronTupla,  # case (x, y):
                    _patronLista,  # case [x, y]:
                    _patronClase,  # case Punto(x, y):
                    _patronGuarda,  # case x if condicion:
                ]
            )
        ],
    )


def _patronTupla():
    return Nodo("_patronTupla", ["(", _patronElementos, ")"])


def _patronLista():
    return Nodo("_patronLista", ["[", _patronElementos, "]"])


def _patronElementos():
    return Nodo(
        "_patronElementos",
        [
            _patron,
            Nodo.Eleccion([[", ", _patronElementos], _stop]),
        ],
    )


def _patronClase():
    return Nodo(
        "_patronClase", [_variable, "(", Nodo.Eleccion([_patronElementos, _stop]), ")"]
    )


def _patronGuarda():
    return Nodo("_patronGuarda", [_patron, " if ", _condicion])


def _declaracionFuncion():
    return Nodo(
        "_declaracionFuncion",
        [
            Nodo.Eleccion(
                [
                    _declaracionFuncionNormal,
                    _declaracionFuncionAsincrona,
                    _declaracionFuncionGeneradora,
                    _declaracionFuncionLambda,
                ]
            ),
            "\n",
        ],
    )


def _declaracionFuncionNormal():
    return Nodo(
        "_declaracionFuncionNormal",
        [
            "def ",
            _letra,
            _textoLetrasNumeros,
            "(",
            _parametros,
            "):\n",
            Nodo.Tab(Nodo.Eleccion([[_pass], [_codigoFuncion]])),
            "\n",
        ],
    )


def _declaracionFuncionAsincrona():
    return Nodo(
        "_declaracionFuncionAsincrona",
        [
            "async def ",
            _letra,
            _textoLetrasNumeros,
            "(",
            _parametros,
            "):\n",
            Nodo.Tab(Nodo.Eleccion([[_pass], [_codigoFuncionAsincrona]])),
            "\n",
        ],
    )


def _declaracionFuncionGeneradora():
    return Nodo(
        "_declaracionFuncionGeneradora",
        [
            "def ",
            _letra,
            _textoLetrasNumeros,
            "(",
            _parametros,
            "):\n",
            Nodo.Tab(_codigoGenerador),
            "\n",
        ],
    )


def _declaracionFuncionLambda():
    return Nodo(
        "_declaracionFuncionLambda",
        [
            "lambda ",
            _argumentosLambda,
            ": ",
            _expresionSimple,
        ],
    )


def _argumentosLambda():
    return Nodo(
        "_argumentosLambda",
        [
            Nodo.Eleccion(
                [
                    _stop,
                    _listaArgumentosLambda,
                ]
            )
        ],
    )


def _listaArgumentosLambda():
    return Nodo(
        "_listaArgumentosLambda",
        [
            _argumentoLambda,
            Nodo.Eleccion(
                [
                    [
                        ", ",
                        _listaArgumentosLambda,
                    ],
                    _stop,
                ]
            ),
        ],
    )


def _argumentoLambda():
    return Nodo(
        "_argumentoLambda",
        [
            Nodo.Eleccion(
                [
                    _variable,
                    [_variable, "=", _dato],
                    ["*", _variable],
                    ["**", _variable],
                ]
            )
        ],
    )


def _expresionSimple():
    return Nodo(
        "_expresionSimple",
        [
            Nodo.Eleccion(
                [
                    _dato,
                    _operacion,
                ]
            )
        ],
    )


def _expresionTernaria():
    return Nodo(
        "_expresionTernaria",
        [
            _dato,
            " if ",
            _condicion,
            " else ",
            _dato,
        ],
    )


def _declaracionMetodo():
    return Nodo(
        "_declaracionMetodo",
        [
            Nodo.Eleccion(
                [
                    _declaracionMetodoNormal,
                    _declaracionMetodoAsincrono,
                    _declaracionMetodoEstatico,
                    _declaracionMetodoClase,
                ]
            ),
            Nodo.Eleccion([_declaracionMetodo, _stop]),
        ],
    )


def _declaracionMetodoNormal():
    return Nodo(
        "_declaracionMetodoNormal",
        [
            "def ",
            _letra,
            _textoLetrasNumeros,
            "(self",
            Nodo.Eleccion([[", ", _parametros], _stop]),
            "):\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _declaracionMetodoAsincrono():
    return Nodo(
        "_declaracionMetodoAsincrono",
        [
            "async def ",
            _letra,
            _textoLetrasNumeros,
            "(self",
            Nodo.Eleccion([[", ", _parametros], _stop]),
            "):\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncionAsincrona])),
            "\n",
        ],
    )


def _declaracionMetodoEstatico():
    return Nodo(
        "_declaracionMetodoEstatico",
        [
            "@staticmethod\n",
            "def ",
            _letra,
            _textoLetrasNumeros,
            "(",
            _parametros,
            "):\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _declaracionMetodoClase():
    return Nodo(
        "_declaracionMetodoClase",
        [
            "@classmethod\n",
            "def ",
            _letra,
            _textoLetrasNumeros,
            "(cls",
            Nodo.Eleccion([[", ", _parametros], _stop]),
            "):\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _clase():
    return Nodo(
        "_clase",
        [
            Nodo.Eleccion(
                [
                    _declaracionClase,
                    _instanciacionClase,
                    _usarClase,
                ]
            )
        ],
    )


def _usarClase():
    return Nodo(
        "_usarClase",
        [
            Nodo.Eleccion(
                [
                    _invocarMetodo,
                    _atributoClase,
                ]
            )
        ],
    )


def _atributoClase():
    return Nodo(
        "_atributoClase",
        [
            Nodo.Eleccion(
                [
                    _leerAtributoClase,
                    _escribirAtributoClase,
                ]
            )
        ],
    )


def _leerAtributoClase():
    return Nodo(
        "_leerAtributoClase",
        [
            _variable,
            ".",
            _variable,
        ],
    )


def _escribirAtributoClase():
    return Nodo(
        "_escribirAtributoClase",
        [
            _variable,
            ".",
            _variable,
            " = ",
            _dato,
        ],
    )


#######

#######


def _herencia():
    return Nodo(
        "_herencia",
        [
            _letra,
            _textoLetrasNumeros,
            Nodo.Eleccion([[", ", _herencia], _stop]),
        ],
    )


def _constructorClase():
    return Nodo(
        "_constructorClase",
        [
            "def __init__(self",
            Nodo.Eleccion([[", ", _parametros], _stop]),
            "):\n",
            Nodo.Tab(Nodo.Eleccion([_pass, _codigoFuncion])),
            "\n",
        ],
    )


def _pass():
    return Nodo("_pass", [Nodo.Eleccion(["pass", "..."])])


def _atributosClase():
    return Nodo(
        "_atributosClase",
        [Nodo.Eleccion([[_variable, " = ", _dato, "\n", _atributosClase], _stop])],
    )


def _builtinOtrosUtilidad():
    return Nodo(
        "_builtinOtrosUtilidad",
        [
            Nodo.Eleccion(
                [
                    ["len(", _argumentos, ")"],
                    ["all(", _argumentos, ")"],
                    ["any(", _argumentos, ")"],
                    ["zip(", _argumentos, ")"],
                    ["slice(", _argumentos, ")"],
                    ["super(", _argumentos, ")"],
                    ["object(", _argumentos, ")"],
                    ["staticmethod(", _argumentos, ")"],
                    ["classmethod(", _argumentos, ")"],
                    ["property(", _argumentos, ")"],
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
                    ["eval(", _argumentos, ")"],
                    ["exec(", _argumentos, ")"],
                    ["compile(", _argumentos, ")"],
                    ["__import__(", _argumentos, ")"],
                ]
            )
        ],
    )


def _builtinOtros():
    return Nodo(
        "_builtinOtros",
        [Nodo.Eleccion([_builtinOtrosUtilidad, _builtinOtrosEjecucion])],
    )


def _builtinIOFichero():
    return Nodo(
        "_builtinIOFichero",
        [
            Nodo.Eleccion(
                [
                    ["open(", _argumentos, ")"],
                    ["read(", _argumentos, ")"],
                    ["write(", _argumentos, ")"],
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
                    ["print(", _argumentos, ")"],
                    ["input(", _argumentos, ")"],
                    ["format(", _argumentos, ")"],
                ]
            )
        ],
    )


def _builtinIO():
    return Nodo("_builtinIO", [Nodo.Eleccion([_builtinIOTexto, _builtinIOFichero])])


def _builtinInspeccionAtributos():
    return Nodo(
        "_builtinInspeccionAtributos",
        [
            Nodo.Eleccion(
                [
                    ["hasattr(", _argumentos, ")"],
                    ["getattr(", _argumentos, ")"],
                    ["setattr(", _argumentos, ")"],
                    ["delattr(", _argumentos, ")"],
                    ["dir(", _argumentos, ")"],
                    ["vars(", _argumentos, ")"],
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
                    ["type(", _argumentos, ")"],
                    ["isinstance(", _argumentos, ")"],
                    ["issubclass(", _argumentos, ")"],
                    ["callable(", _argumentos, ")"],
                ]
            )
        ],
    )


def _builtinInspeccion():
    return Nodo(
        "_builtinInspeccion",
        [Nodo.Eleccion([_builtinInspeccionTipos, _builtinInspeccionAtributos])],
    )


def _builtinIteracionFuncional():
    return Nodo(
        "_builtinIteracionFuncional",
        [
            Nodo.Eleccion(
                [
                    ["map(", _argumentos, ")"],
                    ["filter(", _argumentos, ")"],
                    ["reduce(", _argumentos, ")"],
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
                    ["range(", _argumentos, ")"],
                    ["enumerate(", _argumentos, ")"],
                    ["zip(", _argumentos, ")"],
                    ["reversed(", _argumentos, ")"],
                    ["sorted(", _argumentos, ")"],
                    ["iter(", _argumentos, ")"],
                    ["next(", _argumentos, ")"],
                ]
            )
        ],
    )


def _builtinIteracion():
    return Nodo(
        "_builtinIteracion",
        [Nodo.Eleccion([_builtinIteracionBasica, _builtinIteracionFuncional])],
    )


def _builtinMatematicasAvanzadas():
    return Nodo(
        "_builtinMatematicasAvanzadas",
        [Nodo.Eleccion([["hash(", _argumentos, ")"], ["id(", _argumentos, ")"]])],
    )


def _builtinMatematicasBasicas():
    return Nodo(
        "_builtinMatematicasBasicas",
        [
            Nodo.Eleccion(
                [
                    ["abs(", _argumentos, ")"],
                    ["round(", _argumentos, ")"],
                    ["min(", _argumentos, ")"],
                    ["max(", _argumentos, ")"],
                    ["sum(", _argumentos, ")"],
                    ["pow(", _argumentos, ")"],
                    ["divmod(", _argumentos, ")"],
                ]
            )
        ],
    )


def _builtinMatematicas():
    return Nodo(
        "_builtinMatematicas",
        [Nodo.Eleccion([_builtinMatematicasBasicas, _builtinMatematicasAvanzadas])],
    )


def _builtinConversionTexto():
    return Nodo(
        "_builtinConversionTexto",
        [
            Nodo.Eleccion(
                [
                    ["str(", _argumentos, ")"],
                    ["repr(", _argumentos, ")"],
                    ["ascii(", _argumentos, ")"],
                    ["chr(", _argumentos, ")"],
                    ["ord(", _argumentos, ")"],
                    ["hex(", _argumentos, ")"],
                    ["oct(", _argumentos, ")"],
                    ["bin(", _argumentos, ")"],
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
                    ["list(", _argumentos, ")"],
                    ["tuple(", _argumentos, ")"],
                    ["set(", _argumentos, ")"],
                    ["frozenset(", _argumentos, ")"],
                    ["dict(", _argumentos, ")"],
                    ["bytes(", _argumentos, ")"],
                    ["bytearray(", _argumentos, ")"],
                ]
            )
        ],
    )


def _builtinConversionNumerico():
    return Nodo(
        "_builtinConversionNumerico",
        [
            Nodo.Eleccion(
                [
                    ["int(", _argumentos, ")"],
                    ["float(", _argumentos, ")"],
                    ["complex(", _argumentos, ")"],
                    ["bool(", _argumentos, ")"],
                ]
            )
        ],
    )


def _builtinConversion():
    return Nodo(
        "_builtinConversion",
        [
            Nodo.Eleccion(
                [
                    _builtinConversionNumerico,
                    _builtinConversionSecuencia,
                    _builtinConversionTexto,
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
                    _builtinTipos,
                    _builtinConversion,
                    _builtinMatematicas,
                    _builtinIteracion,
                    _builtinInspeccion,
                    _builtinIO,
                    _builtinOtros,
                ]
            )
        ],
    )


def _declaracionClase():
    return Nodo(
        "_declaracionClase",
        [
            "class ",
            _letra,
            _textoLetrasNumeros,
            Nodo.Eleccion([["(", _herencia, ")"], _stop]),
            ":\n",
            Nodo.Tab(_atributosClase),
            "\n",
            Nodo.Tab(_constructorClase),
            "\n",
            Nodo.Tab(_funcionesClase),
            "\n",
        ],
    )


def _instanciacionClase():
    return Nodo(
        "_instanciacionClase",
        [
            _variable,
            " = ",
            _letra,
            _textoLetrasNumeros,
            "(",
            Nodo.Eleccion([[_argumentos], _stop]),
            ")",
        ],
    )


def _encadenarMetodo():
    return Nodo(
        "_encadenarMetodo",
        [
            _variable,
            "(",
            Nodo.Eleccion([_argumentos, _stop]),
            ")",
            Nodo.Eleccion([[".", _encadenarMetodo], _stop]),
        ],
    )


def _raise():
    return Nodo(
        "_raise",
        [
            "raise",
            Nodo.Eleccion([[" ", Nodo.Eleccion([_llamadaFuncion, _variable])], _stop]),
            "\n",
        ],
    )


def _ejecucion():
    return Nodo(
        "_ejecucion",
        [
            Nodo.Eleccion(
                [
                    _llamadaFuncion,
                    _invocarMetodo,
                    _builtin,
                ]
            )
        ],
    )


def _funcion():
    return Nodo(
        "_funcion",
        [
            Nodo.Eleccion(
                [
                    _declaracionFuncion,
                    _llamadaFuncion,
                ]
            )
        ],
    )


def _llamadaFuncion():
    return Nodo(
        "_llamadaFuncion",
        [
            _variable,
            "(",
            Nodo.Eleccion(
                [
                    [_argumentos],
                    _stop,
                ]
            ),
            ")",
        ],
    )


def _invocarMetodo():
    return Nodo(
        "_invocarMetodo",
        [
            Nodo.Eleccion(
                [
                    _variable,
                    _llamadaFuncion,
                ]
            ),
            ".",
            _encadenarMetodo,
        ],
    )


def _none():
    return Nodo("_none", ["None"])


def _elipsis():
    return Nodo("_elipsis", ["..."])


def _stop():
    return Nodo("_stop", [""])
