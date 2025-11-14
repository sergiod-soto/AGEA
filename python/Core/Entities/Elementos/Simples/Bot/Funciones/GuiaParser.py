guiaArray = {
    "programa": 0,
    "asignacion": 1,
    "control": 2,
    "bucle": 3,
    "for": 4,
    "while": 5,
    "break": 6,
    "continue": 7,
    "condicional": 8,
    "if": 9,
    "elif": 10,
    "else": 11,
    "condicion": 12,
    "controlFunciones": 13,
    "return": 14,
    "yield": 15,
    "controlEstructural": 16,
    "try": 17,
    "finally": 18,
    "with": 19,
    "declaracionEstructural": 20,
    "funcion": 21,
    "argumentos": 22,
    "argumento": 23,
    "clases":24,
    "clase": 25,
    "variablesClase": 26,
    "constructor": 27,
    "funcionesClase": 28,
    "operacion": 29,
    "operacionAritmetica": 30,
    "operacionSuma": 31,
    "comparacion": 32,
    "true": 33,
    "false": 34,
    "operacionBitwise": 35,
    "mascaraAnd": 36,
    "mascaraOr": 37,
    "mascaraNot": 38,
    "mascaraShiftIzquierda": 39,
    "mascaraShiftDerecha": 40,
    "comentario": 41,
    "funciones": 42,
    "declaracionVariablesGlobales": 43,
    "codigo": 44,
    "variable":	45,
    "textoLetrasNumeros": 46,
    "textos": 47,
    "textoLetras": 48,
    "textoLetrasSimbolos": 49,
    "letra": 50,
    "minuscula": 51,
    "mayuscula": 52,
    "digito": 53,
    "simbolo": 54,
    "simboloAritmetico": 55,
    "simboloSuma": 56,
    "simboloResta": 57,
    "simboloMultiplicacion": 58,
    "simboloDivision": 59,
    "simboloModulo": 60,
    "simboloPotencia": 61,
    "simboloLogico": 62,
    "and": 63,
    "or": 64,
    "not": 65,
    "simboloComparacion": 66,
    "equal": 67,
    "notEqual": 68,
    "greaterThan": 69,
    "lowerThan": 70,
    "greaterOrEqualThan": 71,
    "lowerOrEqualThan": 72,
    "parentesis": 73,
    "corchetes": 74,
    "llaves": 75,
    "comillas": 76,
    "char": 77,
    "palabra": 78,
    "string": 79,
    "dato": 80,
    "numero":81,
    "positivo": 82,
    "negativo": 83,
    "integer": 84,
    "double": 85,
    "complex": 86,
    "bool": 87,
    "true": 88,
    "false": 89,
    "conjunto": 90,
    "lista": 91,
    "tupla": 92,
    "diccionario":	93,
    "argumentosKV": 94,
    "argumentoKV": 95,
    "set": 96,
    "simboloTexto": 97,
    "arroba": 98,
    "ampersand": 99,
    "espacio": 100,
    "empty": 101
}

guia = [
    # 0, programa
    [
		"#---------------------------------",
		"\\n",
		"# Variables globales:",
		"\\n",
		"#---------------------------------",
		"\\n",
		"declaracionVariablesGlobales",
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
		"clases",
		"\\n",
		"#---------------------------------",
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
		"funciones",
		"\\n",
		"#---------------------------------",
        "\\n",
        "#---------------------------------",
		"\\n",
		"\\n",
		"\\n",
		"#---------------------------------",
		"\\n",
		"# Codigo:",
		"\\n",
		"#---------------------------------",
		"\\n",
		"codigo",
        "\\n",
        "#---------------------------------",
        "\\n",
        "#---------------------------------"
    ],
    
    # 1, asignacion
    [
        "variable",
        " = ",
        "\\e",
        [
            ["dato"],
            ["variable"],
            ["funcion"],
            ["operacion"]
        ],
        ";",
        "\\n"
    ],
    
    # 2, control
    [
        "\\e",
        [
            ["bucle"],
            ["condicional"],
            ["controlFunciones"],
            ["controlEstructura"],
            ["declaracionEstructural"]
        ]
    ],
    
    # 3, bucle
    [
        "\\e",
        [
            ["for"],
            ["while"],
            ["break"],
            ["continue"]
        ]
    ],
    
    # 4, for
    [
        "for ",
        "\\:integer:variable",
        ", ",
        "variable",
        " in enumerate(",
        "enumerable",
        ", start=",
        "integer",
        "):",
        "\\n",
        "\\t",
        "codigo",
        "\\r"
        "\\n",
        "\\e",
        [
            ["else"],
            ["empty"]
        ],
        "\\n"
    ],
    
    # 5, while
    [
        "while ",
        "condicion",
        ":",
        "\\n",
        "\\t",
        "codigo",
        "\\r",
        "\\n",
        "\\e",
        [
            [
                "\\n",
                "else"
            ],
            ["empty"]
        ],
        "\\n"
    ],
    
    # 6, break
    [
        "break;"
    ],
    
    # 7, continue
    [
        "continue;"
    ],
    
    # 8, condicional
    [
        "if"
    ],
    
    # 9, if
    [
        "if ",
        "condicion",
        ":",
        "\\n",
        "\\t",
        "codigo",
        "\\r",
        "\\n",
        "\\e",
        [
            ["else"],
            ["elif"],
            ["empty"]
        ]
    ],
    
    # 10, elif
    [
        "elif ",
        "condicion",
        ":",
        "\\n",
        "\\t",
        "codigo",
        "\\r",
        "\\n",
        "\\e",
        [
            ["else"],
            ["elif"],
            ["empty"]
        ],
        "\\n"
    ],
    
    # 11, else
    [
        "else:",
        "\\n",
        "\\t",
        "codigo",
        "\\r",
        "\\n"
    ],
    
    # 12, condicion
    [
        "(",
        "dato",
        " ",
        "comparacion",
        ", ",
        "dato",
        ")"
    ],
    
    # 13, controlFunciones
    [
        "\\e",
        [
            ["return"],
            ["yield"]
        ]
    ],

    # 14, return
    [
        "return ",
        "\\e",
        [
            [
                " ",
                "\\e",
                    [
                        ["dato"],
                        ["funcion"]
                    ]
            ],
            ["empty"]
        ],
        ";",
        "\\n"
    ],
    
    # 15, yield
    [
        "yield ",
        " ",
        "\\e",
        [
            ["dato"],
            ["funcion"]
        ],
        ";",
        "\\n"
    ],
    
    # 16, controlEstructural
    [
        "try"
    ],
    
    # 17, try
    [
        "try:",
        "\\n",
        "\\t",
        "codigo",
        "\\r",
        "\\n",
        "\\e",
        [
            [
                "except:",
                "\\n",
                "\\t",
                "codigo",
                "\\r",
                "\\n",
                "\\e",
                [
                    [
                        "\\e",
                        [
                            ["else"],
                            ["finally"],
                            [
                                "else",
                                "finally"
                            ]
                        ]
                    ],
                    ["empty"],
                ]
            ],
            ["empty"],
        ],
        "\\n"
    ],

    # 18, finally
    [
        "finally:",
        "\\n",
        "\\t",
        "codigo",
        "\\r",
        "\\n"
    ],
    
    # 19, with
    [
        "with open(",
        "directorio",
        "\\e",
        [
            ["r"],
            ["w"]
        ],
        ") as ",
        "variable",
        ":",
        "\\n",
        "codigo"
    ],
    
    # 20, declaracionEstructural
    [
        "\\e",
        [
            ["funcion"],
            ["clase"]
        ]
    ],
    
    # 21, funcion
    [
        "def ",
        "textoLetrasNumeros",
        "(",
        "argumentos",
        "):",
        "\\n",
        "\\t",
        "\\e",
        [
            ["pass"],
            ["codigo"]
        ],
        "\\r",
        "\\n"
    ],
    
    # 22, argumentos
    [
        "\\e",
        [
            [
            "argumento",
            ", ",
            "argumentos"
            ],
            ["empty"]
        ]
    ],
    
    # 23, argumento
    [
        "\\e",
        [
            ["dato"],
            ["funcion"]
        ]
    ],
    
    # 24, clases
    [
        "\\e",
        [
            [
                "clase",
                "\\n",
                "clases"
            ],
            ["empty"]
        ]
    ],
    
    # 25, clase
    [
        "class ",
        "textoLetrasNumeros",
        ":",
        "\\n",
        "\\t",
        "atributosClase",
        "\\n",
        "constructor",
        "\\n",
        "funcionesClase",
        "\\r",
        "\\n",
        ";"
    ],
    
    # 26, variablesClase
    [
        "\\e",
        [
            [
            "variable",
            "variablesClase"
            ],
            ["empty"]
        ]
    ],
    
    # 27, constructor
    [
        "def",
        " __init__(self,",
        "atributos",
        "):"
        # TODO
    ],

    # 28, funcionesClase
    [
        "funcion",
        "\\e",
        [
            ["funciones"],
            ["empty"]
        ]
    ],
    
    # 29, operacion
    [
        "\\e",
        [
            ["operacionAritmetica"],
            ["operacionLogica"],
            ["operacionBitwise"]
        ]
    ],
    
    # 30, operacionAritmetica 
    # TODO: Completar operaciones
    [
        "\\e",
        [
            ["suma"],
            ["resta"],
            ["multiplicacion"],
            ["division"],
            ["modulo"],
            ["potencia"],
            ["raiz"]
        ]
    ],
    
    # 31, operacionSuma
    [
        "\\e",
        [
            ["numero"],
            ["\\:integer:funcion"],
            ["operacion"]
        ],
        " + ",
        "\\e",
        [
            ["numero"],
            ["\\:intenger:funcion"],
            ["operacion"]
        ]
    ],

    # 32, comparacion
    [
        "(",
        "\\e",
        [
            ["funcion"],
            ["dato"]
        ],
        " ",
        "simboloComparacion",
        " ",
        "\\e",
        [
            ["funcion"],
            ["dato"]
        ],
        ")"
    ],

    # 33, true
    [
        "true "
    ],

    # 34, false
    [
        "false "
    ],
    
    # 35, operacionBitwise
    [
        "\\e",
        [
            ["mascaraAnd"],
            ["mascaraOr"],
            ["mascaraNot"],
            ["mascaraShiftIzquierda"],
            ["mascaraShiftDerecha"]
        ]
    ],
    
    # 36, mascaraAnd
    [
        "dato",
        "&",
        "\\e",
        [
            ["integer"],
            ["\\:integer:funcion"],
            ["\\:integer:variable"]
        ]
    ],
    
    # 37, mascaraOr
    [
        "|"
    ],
    
    # 38, mascaraNot
    [
        "~"
    ],
    
    # 39, mascaraShiftIzquierda
    [
        "<<"
    ],
    
    # 40, mascaraShiftDerecha
    [
        ">>"
    ],
    
    # 41, comentario
    [
        "'''",
        "\\n",
        "textoConSimbolos",
        "\\n",
        "'''"
    ],

    # 42, funciones
    [
       "\\e",
        [
            [
                "funcion",
                "\\n",
                "funciones"
            ],
            ["empty"]
        ]
    ],

    # 43, declaracionVariablesGlobales
    [
        "\\e",
        [
            [
                "variable",
                ";",
                "\\n",
                "declaracionVariablesGlobales"
            ],
            ["empty"]
        ]
    ],
    
    # 44,codigo
    [
        "\\e",
        [
            [
               "\\e",
               [
                    ["operacion"],
                    ["asignacion"],
                    ["control"],
                    ["funcion"],
                    ["comentario"],
                    ["clase"]
               ],
               ["codigo"]
            ],
            ["empty"]
        ]
    ],
    
    # 45, variable
    [
		"letra",
		"textoLetrasNumeros"
	],
    
    # 46, textoLetrasNumeros
    [
        "letra",
        "digito",
        "\\e",
        [
            ["textoLetrasNumeros"],
            ["empty"]
        ]
    ],
    
    # 47, textos
    [
		"\\e",
		[
			["textoLetras"],
			["textoLetrasNumeros"],
			["textoLetrasSimbolos"]
		]
	],
    
    # 48, textoLetras
    [
		"letra",
		"\\e",
		[
			["textoLetras"],
			["empty"]
		]
	],
    
    # 49, textoLetrasSimbolos
    [
		"\\e",
		[
			["letra"],
			["simbolo"]
		],
		"\\e",
		[
			["textoLetrasSimbolos"],
			["empty"]
		]
	],
    
    # 50, letra
    [
		"\\e",
		[
			["minuscula"],
            ["mayuscula"]
		]
	],
    
    # 51, minuscula
    [
        "\\e",
        [
            ["a"],
			["b"],
			["c"],
			["d"],
			["e"],
			["f"],
			["g"],
			["h"],
			["i"],
			["j"],
			["k"],
			["l"],
			["m"],
			["n"],
			["ñ"],
			["o"],
			["p"],
			["q"],
			["r"],
			["s"],
			["t"],
			["u"],
			["v"],
			["w"],
			["x"],
			["y"],
            ["z"]
        ]
    ],
    
    # 52, mayuscula
    [
        "\\e",
        [
            ["A"],
			["B"],
			["C"],
			["D"],
			["E"],
			["F"],
			["G"],
			["H"],
			["I"],
			["J"],
			["K"],
			["L"],
			["M"],
			["N"],
			["Ñ"],
			["O"],
			["P"],
			["Q"],
			["R"],
			["S"],
			["T"],
			["U"],
			["V"],
			["W"],
			["X"],
			["Y"],
			["Z"]
        ]
    ],
    
    # 53, digito
    [
		"\\e",
        [
            ["0"],
            ["1"],
            ["2"],
            ["3"],
            ["4"],
            ["5"],
            ["6"],
            ["7"],
            ["8"],
            ["9"]
        ]
	],
    
    # 54, simbolo
    [
        "\\e",
        [
            ["simboloAritmetico"],
            ["simboloLogico"],
            ["simboloComparacion"],
            ["simboloTexto"],
            ["parentesis"],
            ["corchetes"],
            ["llaves"],
            ["comillas"]
        ]
    ],
    
    # 55, simboloAritmetico
    [
		"\\e",
		[
			["simboloSuma"],
			["simboloResta"],
			["simboloMultiplicacion"],
			["simboloDivision"],
			["simboloModulo"],
			["simboloPotencia"]
		]
	],
    
    # 56, simboloSuma
    [
		"+"
	],
    
    # 57, simboloResta
    [
		"-"
	],
    
    # 58, simboloMultiplicacion
    [
		"*"
	],
    
    # 59, simboloDivision
    [
		"/"
	],
    
    # 60, simboloModulo
    [
		"%"
	],
    
    # 61, simboloPotencia
    [
		"**"
	],
    
    # 62, simboloLogico
    [
		"\\e",
		[
			["and"],
			["or"],
			["not"]
		]
	],
    
    # 63, and
    [
		"and "
	],
    
    # 64, or
    [
		"or "
	],
    
    # 65, not
    [
		"not "
	],
    
    # 66, simboloComparacion
    [
		"\\e",
		[
			["equal"],
			["notEqual"],
			["greaterThan"],
			["lowerThan"],
			["greaterOrEqualThan"],
			["lowerOrEqualThan"]
		]
	],
    
    # 67, equal
    [
		"=="
	],
    
    # 68, notEqual
    [
		"!="
	],
    
    # 69, greaterThan
    [
		">"
	],
    
    # 70, lowerThan
    [
		"<"
	],
    
    # 71, greaterOrEqualThan
    [
		">="
	],
    
    # 72, lowerOrEqualThan
    [
		"<="
	],
    
    # 73, parentesis
    [
		"\\e",
		[
			["("],
			[")"]
		]
	],
    
    # 74, corchetes
    [
		"\\e",
		[
			["["],
			["]"]
		]
	],
    
    # 75, llaves
    [
		"\\e",
		[
			["{"],
			["}"]
		]
	],
    
    # 76, comillas
    [
		"\""
	],
    
    # 77, char
    [
		"\\e",
		[
			["letra"],
			["simbolo"]
		]
	],
    
    # 78, palabra
    [
		"char",
		"\\e",
		[
			["palabra"],
			["empty"]
		]
	],
    
    # 79, string
    [
		"\"",
		"palabra",
		"\""
	],
    
    # 80, dato
    [
		"\\e",
		[
			["numero"],
			["string"],
			["bool"],
			["conjunto"],
			["variable"],
		]
	],
    
    # 81, numero
    [
        "\\e",
        [
            ["positivo"],
            ["negativo"]
        ],
        "\\e",
        [
            ["integer"],
            ["double"],
            ["complex"]
        ]	
    ],
    
    # 82, positivo
    [
		""
	],
    
    # 83, negativo
    [
		"-"
	],
    
    # 84, integer
    [
        "digito",
        "\\e",
        [
            ["integer"],
            ["empty"]
        ]
    ],
    
    # 85, double
    [
		"integer",
		".",
		"integer"
	],
    
    # 86, complex
    [
		"complex("
		"\\e",
		[
			["positivo"],
			["negativo"]
		],
		"\\e",
		[
			["integer"],
			["double"]
		],
		", ",
		"\\e",
		[
			["positivo"],
			["negativo"]
		],
		"\\e",
		[
			["integer"],
			["double"]
		],
		")"
	],
    
    # 87, bool
    [
		"\\e",
		[
			["true"],
			["false"]
		]
	],
    
    # 88, true
    [
		"True"
	],
    
    # 89, false
    [
		"False"
	],
    
    # 90, conjunto
    [
		"\\e",
		[
			["lista"],
			["tupla"],
			["diccionario"],
			["set"]
		]
	],
    
    # 91, lista
    [
		"variable",
		" = ",
		"[",
		"argumentos",
		"];",
		"\\n"
	],
    
    # 92, tupla
    [
		"variable",
		" = ",
		"(",
		"argumentos",
		")",
		"\n"
	],
    
    # 93, diccionario
    [
		"variable",
		" = ",
		"{",
		"argumentosKV",
		"}",
		"\n"
	],
    
    # 94, argumentosKV
    [
		"\\e",
		[
			[
				"argumentoKV",
				", ",
				"argumentosKV"
			], 	
			["empty"]
		]
	],
    
    # 95, argumentoKV
    [
		"\\e",
		[
			[
				"string",
				": ",
				"dato",
			],
			[
				"string",
				": ",
				"funcion",
			]
		]
	],
    
    # 96, set
    [
		"variable",
		" = ",
		"{",
		"argumentos",
		"}"
	],
    
    # 97, simboloTexto
    [
        "\\e",
        [
            "arroba",
            "ampersand",
            "espacio"
        ]
    ],
    
    # 98, arroba
    [
        "@"
    ],
    
    # 99, ampersand
    [
        "&"
    ],
    
    # 100, espacio
    [
        " "
    ],

    # 101, empty
    [
        ""
    ]
]
