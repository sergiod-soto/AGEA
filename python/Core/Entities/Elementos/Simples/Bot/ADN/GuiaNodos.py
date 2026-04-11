class Eleccion:
    
    def __init__(self, opciones: list):
        self.opciones = opciones
        
class Nodo:
    
    def __init__(self, nombre: str, contenido: list):
        self.nombre = nombre
        self.contenido = contenido

guia_old = {
    "programa": [
        "codigoInyectado",
        "\\n",
        "\\n",
        "#------------",
        "\\n",
        "# FIN IMPORTS LIBRERIAS POST ANALISIS",
        "\\n",
        "from functools import reduce",
        "\\n",
        "#-----------",
        "\\n",
        "#-----------",
        "\\n",
        "\\n",
        "\\n",
        "#-----------",
        "\\n",
        "# Clases:",
        "\\n",
        "#-----------",
        "\\n",
        "clases",
        "\\n",
        "#-----------",
        "\\n",
        "\\n",
        "\\n",
        "#-----------",
        "\\n",
        "# Funciones:",
        "\\n",
        "#-----------",
        "\\n",
        "funciones",
        "\\n",
        "#-----------",
        "\\n",
        "# Variables globales:",
        "\\n",
        "#-----------",
        "\\n",
        "declaracionVariablesGlobales",
        "\\n",
        "\\n",
        "\\n",
        "#-----------",
        "\\n",
        "# Codigo:",
        "\\n",
        "#-----------",
        "\\n",
        "codigo",
    ],
    "asignacion": [
        "variable",
        " = ",
        "\\e",
        ["dato", "variable", "llamadaFuncion", "operacion"],
        "\\n",
    ],
    "control": [
        "\\e",
        [
            "bucle",
            "condicional",
            "controlFunciones",
            "controlEstructura",
            "declaracionEstructural",
        ],
    ],
    "bucle": ["\\e", ["for", "while", "break", "continue"]],
    "for": ["\\e",["forLista", "forIndice", "forNumerico", "forDict"]],
    "condicional": ["\\e", ["if", "match"]],
    "if": [
        "if ",
        "condicion",
        ":",
        "\\n",
        "\\t",
        "codigo",
        "\\n",
        "\\e",
        ["else", "elif", "\\e"],
    ],
    "elif": [
        "elif ",
        "condicion",
        ":",
        "\\n",
        "\\t",
        "codigo",
        "\\n",
        "\\e",
        ["else", "elif", "\\e"],
        "\\n",
    ],
    "else": ["else:", "\\n", "\\t", "codigo", "\\n"],
    "condicion": ["(", "dato", " ", "comparacion", " ", "dato", ")"],
    "controlFunciones": ["\\e", ["return", "yield"]],
    "return": [
        "return ",
        "\\e",
        [
            ["\\e", 
                ["dato", "llamadaFuncion"]
            ], 
            "\\e"
        ],
        "\\n",
    ],
    "yield": ["yield ", " ", "\\e", ["dato", "llamadaFuncion"], "\\n"],
    "controlEstructural": ["try"],
    "try": [
        "try:",
        "\\n",
        "\\tcodigo",
        "\\n",
        "\\e",
        [
            "\\e",
            [
                "except:",
                "\\n",
                "\\tcodigo",
                "\\n",
                "\\e",
                ["\\e", "\\e", ["else", "finally", ["else", "finally"]]],
            ],
        ],
        "\n",
    ],
    "finally": ["finally:", "\\n", "\\t", "codigo", "\\n"],
    "with": [
        "with open(",
        "directorio",
        "\\e",
        ["r", "w"],
        ") as ",
        "variable",
        ":",
        "\\n",
        "codigo",
    ],
    "declaracionEstructural": ["\\e", ["llamadaFuncion", "clase"]],
    "argumentos": ["\\e", [["argumento", ", ", "argumentos"], "\\e"]],
    "argumento": ["\\e", ["dato", "llamadaFuncion"]],
    "variablesClase": ["\\e", [["variable", "variablesClase"], "\\e"]],
    "funcionesClase": ["funcion", "\\e", ["funciones", "\\e"]],
    "operacion": [
        "\\e",
        ["operacionAritmetica", "operacionLogica", "operacionBitwise"],
    ],
    "operacionAritmetica": [
        "\\e",
        ["suma", "resta", "multiplicacion", "division", "modulo", "potencia", "raiz"],
    ],
    "suma": [
        "\\e",
        ["_numero()", "funcion", "operacion"],
        " + ",
        "\\e",
        ["_numero()", "funcion", "operacion"],
    ],
    "resta": [
        "\\e",
        ["_numero()", "funcion", "operacion"],
        " - ",
        "\\e",
        ["_numero()", "funcion", "operacion"],
    ],
    "multiplicacion": ["_numero()", "simboloMultiplicacion", "_numero()"],
    "division": ["_numero()", "simboloDivision", "_numero()"],
    "modulo": ["_numero()", "simboloModulo", "_numero()"],
    "potencia": ["_numero()", "simboloPotencia", "_numero()"],
    "raiz": ["_numero()", "**(1/", "_numero()", ")"],
    "comparacion": [
        "(",
        "\\e",
        ["funcion", "dato"],
        " ",
        "simboloComparacion",
        " ",
        "\\e",
        ["funcion", "dato"],
        ")",
    ],
    "simboloSuma": ["+"],
    "simboloResta": ["-"],
    "simboloMultiplicacion": ["*"],
    "simboloDivision": ["/"],
    "simboloModulo": ["%"],
    "simboloPotencia": ["**"],
    "true": ["True"],
    "false": ["False"],
    "operacionBitwise": [
        "\\e",
        [
            "mascaraAnd",
            "mascaraOr",
            "mascaraNot",
            "mascaraShiftIzquierda",
            "mascaraShiftDerecha",
        ],
    ],
    "mascaraAnd": ["dato", "&", "dato"],
    "mascaraOr": ["dato", "|", "dato"],
    "mascaraNot": ["~", "dato"],
    "comentario": ["\\e", ["_comentarioLinea()", "_comentarioBloque()"]],
    "_comentarioLinea()": ["# ", "_contenidoComentario()", "\\n"],
    "_comentarioBloque()": ["'''", "\\n", "_contenidoComentario()", "\\n", "'''"],
    "_contenidoComentario()": [
        "\\e",
        ["\\p", "textoLetras"],
        "\\e",
        [[" ", "_contenidoComentario()"], "\\e"],
    ],
    "textoLetrasSimbolos": [
        "\\e",
        ["letra", "simbolo"],
        "\\e",
        ["textoConSimbolos", "\\e"],
    ],
    "textoLetrasNumeros": [
        "\\e",
        ["letra", _digito()],
        "\\e",
        ["textoLetrasNumeros", "\\e"],
    ],
    "textoLetras": ["letra", "\\e", ["textoLetras", "\\e"]],
    "textos": [
        "\\e",
        [
            "textoLetras",
            "textoLetrasNumeros",
            "textoLetrasSimbolos",
            "textoDirectorios",
        ],
    ],
    "variable": ["letra", "textoLetrasNumeros"],
    "funciones": ["funcion", "\\n", "\\e", ["funciones", "\\e"], "\\n"],
    "declaracionVariablesGlobales": [
        "variable",
        "\\n",
        "\\e",
        ["declaracionVariablesGlobales", "\\x"],
        "\\n",
    ],
    "codigo": [
        "\\e",
        ["operacion", "asignacion", "control", "funcion", "comentario", "clase"],
        "\\e",
        ["codigo", "\\x"],
    ],
    "conjunto": ["\\e", ["lista", "tupla", "diccionario", "set"]],
    "set": ["variable", " = ", "{", "argumentos", "}"],
    "diccionario": ["variable", " = ", "{", "argumentosKV", "}", "\n"],
    "argumentosKV": ["\\e", [["argumentoKV", ", ", "argumentosKV"], "\\e"]],
    "argumentoKV": ["\\e", [["string", ": ", "dato"], ["string", ": ", "funcion"]]],
    "tupla": ["(", "argumentos", ")", "\\n"],
    "lista": ["[", "argumentos", "]", "\\n"],
    "bool": ["\\e", ["true", "false"]],
    "string": ['"', "palabra", '"'],
    "palabra": ["char", "\\e", ["palabra", "\\x"]],
    "char": ["\\e", ["letra", "simbolo"]],
    "letra": [
        "\\e",
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
        ],
    ],
    "simbolo": [
        "\\e",
        [
            "simboloAritmetico",
            "simboloLogico",
            "simboloComparacion",
            "parentesis",
            "corchetes",
            "llaves",
            "comillas",
        ],
    ],
    "simboloAritmetico": [
        "\\e",
        [
            "simboloSuma",
            "simboloResta",
            "simboloMultiplicacion",
            "simboloDivision",
            "simboloModulo",
            "simboloPotencia",
        ],
    ],
    "simboloLogico": ["\\e", ["and", "or", "not"]],
    "and": ["and "],
    "or": ["or "],
    "not": ["not "],
    "simboloComparacion": [
        "\\e",
        [
            "_equal()",
            "_notEqual()",
            "_greaterThan()",
            "_lowerThan()",
            "_greaterOrEqualThan()",
            "_lowerOrEqualThan()",
        ],
    ],
    "_equal()": ["=="],
    "_notEqual()": ["!="],
    "_greaterThan()": [">"],
    "_lowerThan()": ["<"],
    "_greaterOrEqualThan()": [">="],
    "_lowerOrEqualThan()": ["<="],
    "parentesis": ["\\e", ["(", ")"]],
    "corchetes": ["\\e", ["[", "]"]],
    "llaves": ["\\e", ["{", "}"]],
    "comillas": ['"'],
    "_numero()": [
        "\\e",
        ["positivo", "negativo"],
        "\\e",
        ["integer", "double", "complex"],
    ],
    "integer": [_digito(), "\\e", ["integer", "\\e"]],
    "double": ["integer", ".", "integer"],
    "complex": [
        "complex(",
        "\\e",
        ["positivo", "negativo"],
        "\\e",
        ["integer", "double"],
        ", ",
        "\\e",
        ["positivo", "negativo"],
        "\\e",
        ["integer", "double"],
        ")",
    ],
    "positivo": [""],
    "negativo": ["-"],
    _digito(): ["\\e", ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]],
    "dato": [
        "\\e",
        [
            "_numero()",
            "string",
            "bool",
            "conjunto",
            "variable",
            "funcion",
            "leerAtributoClase",
            "llamadaFuncion",
            "invocarMetodo",
        ],
    ],
    "operacionLogica": [
        "\\e",
        ["operacionAnd", "operacionOr", "operacionNot", "comparacion", "true", "false"],
    ],
    "operacionAnd": ["(", "comparacion", " ", "and", " ", "comparacion", ")"],
    "operacionOr": ["(", "comparacion", " ", "or", " ", "comparacion", ")"],
    "operacionNot": ["not", "(", "comparacion", ")"],
    "mascaraShiftIzquierda": ["<<", "dato"],
    "mascaraShiftDerecha": [">>", "dato"],
    "forLista": [
        "for ",
        "variable",
        " in ",
        "variable",
        ":",
        "\\n",
        "\\tcodigoFuncion",
        "\\n",
    ],
    "forIndice": [
        "for ",
        "variable",
        ", ",
        "variable",
        " in enumerate(",
        "variable",
        ", start=",
        "integer",
        "):",
        "\\n",
        "\\tcodigoFuncion",
        "\\n",
    ],
    "forNumerico": [
        "for ",
        "variable",
        " in range(",
        "\\e",
        [
            ["\\e", ["integer", "variable", "llamadaFuncion"]],
            [
                "\\e",
                ["integer", "variable", "llamadaFuncion"],
                ", ",
                "\\e",
                ["integer", "variable", "llamadaFuncion"],
            ],
            [
                "\\e",
                ["integer", "variable", "llamadaFuncion"],
                ", ",
                "\\e",
                ["integer", "variable", "llamadaFuncion"],
                ", ",
                "\\e",
                ["integer", "variable", "llamadaFuncion"],
            ],
        ],
        "):",
        "\\n",
        "\\t",
        "codigoBucle",
        "\\n",
        "\\e",
        ["forElse", "\\e"],
    ],
    "forDict": [
        "for ",
        "variable",
        " in ",
        "variable",
        ":",
        "\\n",
        "\\tcodigoFuncion",
        "\\n",
    ],
    "break": ["break ", "\\n"],
    "while": [
        "while ",
        "condicion",
        ":",
        "\\n",
        "\\tcodigo",
        "\\n",
        "\\e",
        ["\\e", ["\\n", "else"]],
        "\\n",
    ],
    "continue": ["continue ", "\\n"],
    "match": [
        "match ",
        "\\e",
        ["variable", "funcion"],
        ":",
        "\\n",
        "cases",
        "\\e",
        [["case _:", "\\n", "codigo"], ["\\e"]],
    ],
    "cases": [
        "case ",
        "palabra",
        ":",
        "\n",
        "\tcodigo",
        "\\n",
        "\\e",
        ["cases", "\\e"],
    ],
    "declaracionFuncion": [
        "\\e",
        ["declaracionFuncionNormal", "declaracionFuncionMetodo"],
        "\\n",
    ],
    "declaracionFuncionNormal": [
        "def ",
        "letra",
        "textoLetrasNumeros",
        "(",
        "argumentos",
        "):",
        "\\n",
        "\\e",
        [["\\t", "pass"], ["\\t", "codigoFuncion"]],
        "\\n",
    ],
    "declaracionFuncionAsincrona": [
        "async def ",
        "letra",
        "textoLetrasNumeros",
        "(",
        "argumentos",
        "):",
        "\\n",
        "\\e",
        [["\\t", "pass"], ["\\t", "codigoFuncionAsincrona"]],
        "\\n",
    ],
    "declaracionFuncionGeneradora": [
        "def ",
        "letra",
        "textoLetrasNumeros",
        "(",
        "argumentos",
        "):",
        "\\n",
        "\\t",
        "codigoGenerador",
        "\\n",
    ],
    "declaracionFuncionLambda": [
        "lambda ",
        "argumentosLambda",
        ": ",
        "expresionSimple",
    ],
    "declaracionMetodo": [
        "\\e",
        [
            "declaracionMetodoNormal",
            "declaracionMetodoAsincrono",
            "declaracionMetodoEstatico",
            "declaracionMetodoClase",
        ],
        "\\e",
        ["declaracionMetodo", "\\e"],
    ],
    "declaracionMetodoNormal": [
        "def ",
        "letra",
        "textoLetrasNumeros",
        "(self",
        "\\e",
        [[", ", "argumentos"], "\\e"],
        "):",
        "\\n",
        "\\e",
        [["\\t", "pass"], ["\\t", "codigoFuncion"]],
        "\\n",
    ],
    "declaracionMetodoAsincrono": [
        "async def ",
        "letra",
        "textoLetrasNumeros",
        "(self",
        "\\e",
        [[", ", "argumentos"], "\\e"],
        "):",
        "\\n",
        "\\e",
        [["\\t", "pass"], ["\\t", "codigoFuncionAsincrona"]],
        "\\n",
    ],
    "declaracionMetodoEstatico": [
        "@staticmethod",
        "\\n",
        "def ",
        "letra",
        "textoLetrasNumeros",
        "(",
        "argumentos",
        "):",
        "\\n",
        "\\e",
        [["\\t", "pass"], ["\\t", "codigoFuncion"]],
        "\\n",
    ],
    "declaracionMetodoClase": [
        "@classmethod",
        "\\n",
        "def ",
        "letra",
        "textoLetrasNumeros",
        "(cls",
        "\\e",
        [[", ", "argumentos"], "\\e"],
        "):",
        "\\n",
        "\\e",
        [["\\t", "pass"], ["\\t", "codigoFuncion"]],
        "\\n",
    ],
    "clase": ["\\e", ["declaracionClase", "instanciacionClase", "usarClase"]],
    "herencia": ["letra", "textoLetrasNumeros", "\\e", [[", ", "herencia"], "\\e"]],
    "metodosClase": [
        "\\e",
        [["declaracionMetodo", "\\n", "\\t", "metodosClase"], "\\e"],
    ],
    "constructorClase": [
        "def __init__(self",
        "\\e",
        [[", ", "argumentos"], "\\e"],
        "):",
        "\\n",
        "\\e",
        [["\\t", "pass"], ["\\t", "codigoFuncion"]],
        "\\n",
    ],
    "atributosClase": [
        "\\e",
        [["variable", " = ", "dato", "\\n", "atributosClase"], "\\e"],
    ],
    "builtinOtrosUtilidad": [
        "\\e",
        [
            ["len(", "argumentos", ")"],
            ["all(", "argumentos", ")"],
            ["any(", "argumentos", ")"],
            ["zip(", "argumentos", ")"],
            ["slice(", "argumentos", ")"],
            ["super(", "argumentos", ")"],
            ["object(", "argumentos", ")"],
            ["staticmethod(", "argumentos", ")"],
            ["classmethod(", "argumentos", ")"],
            ["property(", "argumentos", ")"],
        ],
    ],
    "builtinOtrosEjecucion": [
        "\\e",
        [
            ["eval(", "argumentos", ")"],
            ["exec(", "argumentos", ")"],
            ["compile(", "argumentos", ")"],
            ["__import__(", "argumentos", ")"],
        ],
    ],
    "builtinOtros": ["\\e", ["builtinOtrosUtilidad", "builtinOtrosEjecucion"]],
    "builtinIOFichero": [
        "\\e",
        [
            ["open(", "argumentos", ")"],
            ["read(", "argumentos", ")"],
            ["write(", "argumentos", ")"],
        ],
    ],
    "builtinIOTexto": [
        "\\e",
        [
            ["print(", "argumentos", ")"],
            ["input(", "argumentos", ")"],
            ["format(", "argumentos", ")"],
        ],
    ],
    "builtinIO": ["\\e", ["builtinIOTexto", "builtinIOFichero"]],
    "builtinInspeccionAtributos": [
        "\\e",
        [
            ["hasattr(", "argumentos", ")"],
            ["getattr(", "argumentos", ")"],
            ["setattr(", "argumentos", ")"],
            ["delattr(", "argumentos", ")"],
            ["dir(", "argumentos", ")"],
            ["vars(", "argumentos", ")"],
        ],
    ],
    "builtinInspeccionTipos": [
        "\\e",
        [
            ["type(", "argumentos", ")"],
            ["isinstance(", "argumentos", ")"],
            ["issubclass(", "argumentos", ")"],
            ["callable(", "argumentos", ")"],
        ],
    ],
    "builtinInspeccion": [
        "\\e",
        ["builtinInspeccionTipos", "builtinInspeccionAtributos"],
    ],
    "builtinIteracionFuncional": [
        "\\e",
        [
            ["map(", "argumentos", ")"],
            ["filter(", "argumentos", ")"],
            ["reduce(", "argumentos", ")"],
        ],
    ],
    "builtinIteracionBasica": [
        "\\e",
        [
            ["range(", "argumentos", ")"],
            ["enumerate(", "argumentos", ")"],
            ["zip(", "argumentos", ")"],
            ["reversed(", "argumentos", ")"],
            ["sorted(", "argumentos", ")"],
            ["iter(", "argumentos", ")"],
            ["next(", "argumentos", ")"],
        ],
    ],
    "builtinIteracion": [
        "\\e",
        ["builtinIteracionBasica", "builtinIteracionFuncional"],
    ],
    "builtinMatematicasAvanzadas": [
        "\\e",
        [["hash(", "argumentos", ")"], ["id(", "argumentos", ")"]],
    ],
    "builtinMatematicasBasicas": [
        "\\e",
        [
            ["abs(", "argumentos", ")"],
            ["round(", "argumentos", ")"],
            ["min(", "argumentos", ")"],
            ["max(", "argumentos", ")"],
            ["sum(", "argumentos", ")"],
            ["pow(", "argumentos", ")"],
            ["divmod(", "argumentos", ")"],
        ],
    ],
    "builtinMatematicas": [
        "\\e",
        ["builtinMatematicasBasicas", "builtinMatematicasAvanzadas"],
    ],
    "builtinConversionTexto": [
        "\\e",
        [
            ["str(", "argumentos", ")"],
            ["repr(", "argumentos", ")"],
            ["ascii(", "argumentos", ")"],
            ["chr(", "argumentos", ")"],
            ["ord(", "argumentos", ")"],
            ["hex(", "argumentos", ")"],
            ["oct(", "argumentos", ")"],
            ["bin(", "argumentos", ")"],
        ],
    ],
    "builtinConversionSecuencia": [
        "\\e",
        [
            ["list(", "argumentos", ")"],
            ["tuple(", "argumentos", ")"],
            ["set(", "argumentos", ")"],
            ["frozenset(", "argumentos", ")"],
            ["dict(", "argumentos", ")"],
            ["bytes(", "argumentos", ")"],
            ["bytearray(", "argumentos", ")"],
        ],
    ],
    "builtinConversionNumerico": [
        "\\e",
        [
            ["int(", "argumentos", ")"],
            ["float(", "argumentos", ")"],
            ["complex(", "argumentos", ")"],
            ["bool(", "argumentos", ")"],
        ],
    ],
    "builtinConversion": [
        "\\e",
        [
            "builtinConversionNumerico",
            "builtinConversionSecuencia",
            "builtinConversionTexto",
        ],
    ],
    "builtinTipos": [
        "\\e",
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
        ],
    ],
    "builtin": [
        "\\e",
        [
            "builtinTipos",
            "builtinConversion",
            "builtinMatematicas",
            "builtinIteracion",
            "builtinInspeccion",
            "builtinIO",
            "builtinOtros",
        ],
    ],
    "declaracionClase": [
        "class ",
        "letra",
        "textoLetrasNumeros",
        "\\e",
        [["(", "herencia", ")"], "\\e"],
        ":",
        "\\n",
        "\\t",
        "atributosClase",
        "\\n",
        "\\t",
        "constructor",
        "\\n",
        "\\t",
        "metodosClase",
        "\\n",
    ],
    "instanciacionClase": [
        "variable",
        " = ",
        "letra",
        "textoLetrasNumeros",
        "(",
        "\\e",
        [["argumentos"], "\\e"],
        ")",
    ],
    "usoClase": ["\\e", ["invocarMetodo", "atributoClase"]],
    "encadenarMetodo": [
        "variable",
        "(",
        "\\e",
        [["argumentos"], "\\e"],
        ")",
        "\\e",
        [[".", "encadenarMetodo"], "\\e"],
    ],
    "atributoClase": ["\\e", ["leerAtributoClase", "escribirAtributoClase"]],
    "leerAtributoClase": ["variable", ".", "variable"],
    "escribirAtributoClase": ["variable", ".", "variable", " = ", "dato"],
    "raise": ["raise", "\\e", [[" ", "\\e", ["llamadaFuncion", "variable"]], "\\e"]],
    "ejecucion": [
        "\\e",
        ["funcion", "clase", "builtin", "acessoFichero", "accesoInternet"],
    ],
    "funcion": ["\\e", ["declaracionFuncion", "llamadaFuncion"]],
    "llamadaFuncion": ["variable", "(", "\\e", [["argumentos"], "\\e"], ")"],
    "invocarMetodo": ["\\e", ["variable", "llamadaFuncion"], ".", "encadenarMetodo"],
    "accesoRecurso": ["accesoFichero", "accesoInternet"],
    "accesoFichero": [
        "\\e",
        ["leerFichero", "escribirFichero", "anadirFichero", "leerEscribirFichero"],
    ],
    "leerFichero": [
        "with open(",
        "textoDirectorioLocal",
        ", 'r') as ",
        "variable",
        ":",
        "\\n",
        "\\tcodigoFuncion",
    ],
    "escribirFichero": [
        "with open(",
        "textoDirectorioLocal",
        ", 'w') as ",
        "variable",
        ":",
        "\\n",
        "\\tcodigoFuncion",
    ],
    "anadirFichero": [
        "with open(",
        "textoDirectorioLocal",
        ", 'a') as ",
        "variable",
        ":",
        "\\n",
        "\\tcodigoFuncion",
    ],
    "leerEscribirFichero": [
        "with open(",
        "textoDirectorioLocal",
        ", 'r+') as ",
        "variable",
        ":",
        "\\n",
        "\\tcodigoFuncion",
    ],
    "accesoInternet": ["\\e", ["httpGet", "httpPost"]],
    "httpGet": ["requests.get(", "textoDirectorioWeb", ")"],
    "httpPost": ["requests.post(", "textoDirectorioWeb", ", data=", "dato", ")"],
    "textoDirectorios": ["\\e", ["textoDirectorioLocal", "textoDirectorioWeb"]],
    "textoDirectorioLocal": [
        "\\e",
        ["textoDirectorioWindows", "textoDirectorioLinux", "textoDirectorioMac"],
    ],
    "textoDirectorioWindows": [
        "\\e",
        ["letra", _digito(), "simboloDirectorioWindows"],
        "\\e",
        [["\\\\", "textoDirectorioWindows"], "\\e"],
    ],
    "textoDirectorioLinux": [
        "\\e",
        ["letra", _digito(), "simboloDirectorioLinux"],
        "\\e",
        [["/", "textoDirectorioLinux"], "\\e"],
    ],
    "textoDirectorioMac": [
        "\\e",
        ["letra", _digito(), "simboloDirectorioMac"],
        "\\e",
        [["/", "textoDirectorioMac"], "\\e"],
    ],
    "textoDirectorioWeb": ["\\e", ["urlWeb", "urlLocal"]],
    "urlWeb": [
        "\\e",
        ["http://", "https://"],
        "textoDirectorioExterno",
        "\\e",
        [[".", "textoDirectorioExterno"], "\\e"],
        "\\e",
        [[".", "textoDirectorioExterno"], "\\e"],
        "\\e",
        [["/", "directorioExternoRuta"], "\\e"],
        "\\e",
        [["?", "directorioExternoParametros"], "\\e"],
    ],
    "textoDirectorioExterno": [
        "\\e",
        ["letra", _digito(), "simboloDirectorioExterno"],
        "\\e",
        [["textoDirectorioExterno"], "\\e"],
    ],
    "simboloDirectorioExterno": [
        "\\e",
        ["-", "_", ".", "~", "%", "+", "=", "&", "@", "!", "$", "'"],
    ],
    "directorioExternoRuta": [
        "textoDirectorioExterno",
        "\\e",
        [["/", "directorioExternoRuta"], "\\e"],
    ],
    "directorioExternoParametros": [
        "textoDirectorioExterno",
        "=",
        "textoDirectorioExterno",
        "\\e",
        [["&", "directorioExternoParametros"], "\\e"],
    ],
    "urlLocal": [
        "\\e",
        ["http://", "https://"],
        "\\e",
        ["localhost", "127.0.0.1", "0.0.0.0", "ipLocal"],
        "\\e",
        [[":", "puerto"], "\\e"],
        "\\e",
        [["/", "directorioExternoRuta"], "\\e"],
    ],
    "ipLocal": [
        _digito(),
        "\\e",
        [[_digito()], "\\e"],
        "\\e",
        [[_digito()], "\\e"],
        ".",
        _digito(),
        "\\e",
        [[_digito()], "\\e"],
        "\\e",
        [[_digito()], "\\e"],
        ".",
        _digito(),
        "\\e",
        [[_digito()], "\\e"],
        "\\e",
        [[_digito()], "\\e"],
        ".",
        _digito(),
        "\\e",
        [[_digito()], "\\e"],
        "\\e",
        [[_digito()], "\\e"],
    ],
    "puerto": [
        _digito(),
        "\\e",
        [[_digito()], "\\e"],
        "\\e",
        [[_digito()], "\\e"],
        "\\e",
        [[_digito()], "\\e"],
        "\\e",
        [[_digito()], "\\e"],
    ]
}


 

def _programa(): 
    return Nodo("_programa", [
        _codigoInyectado(),
        "\\n",
        "\\n",
        "# ",
        "-"*12,
        "\\n",
        "# FIN IMPORTS LIBRERIAS POST ANALISIS",
        "\\n",
        "from functools import reduce",
        "\\n",
        "#-----------",
        "\\n",
        "#-----------",
        "\\n",
        "\\n",
        "\\n",
        "#-----------",
        "\\n",
        "# Clases:",
        "\\n",
        "#-----------",
        "\\n",
        _clases(),
        "\\n",
        "#-----------",
        "\\n",
        "\\n",
        "\\n",
        "#-----------",
        "\\n",
        "# Funciones:",
        "\\n",
        "#-----------",
        "\\n",
        _funciones(),
        "\\n",
        "#-----------",
        "\\n",
        "# Variables globales:",
        "\\n",
        "#-----------",
        "\\n",
        _declaracionVariablesGlobales(),
        "\\n",
        "\\n",
        "\\n",
        "#-----------",
        "\\n",
        "# Codigo:",
        "\\n",
        "#-----------",
        "\\n",
        _codigo()
    ])
    
def _asignacion():
    return Nodo("_asignacion", [
        _variable(), 
        " = ", 
        Eleccion( [
            _dato(),      
            _variable(),    
            _llamadaFuncion(),      
            _operacion()   
            ]),   
        "\\n"
    ])
    
def _control():
    return Nodo("_control", [Eleccion(
        [
            _bucle(),
            _condicional(),
            _controlFunciones(),
            _controlEstructura(),
            _declaracionEstructural()
        ])
    ])
    
def _bucle():
    return Nodo("_bucle", [Eleccion(    
        [
            _for(),
            _while(), 
            _break(), 
            _continue()
        ])
    ])
    
def _for():
    return Nodo("_for" , [
        Eleccion(
        [
            _forLista(), 
            _forIndice(), 
            _forNumerico(), 
            _forDict()
        ])
    ])

def _condicional():
    return Nodo("_condicional",  [
        Eleccion( [
            _if(),
            _match()
        ])
    ])
   
def _if():
    return Nodo("_if",[
        "if ",
        condicion,
        ":",
        "\\n",
        "\\t",
        codigo,
        "\\n",
        Eleccion([
            [
                Eleccion([
                    _else(), 
                    _elif()
                ])            
            ],  
            "\\x"
        ])
    ])

def _elif():
    return Nodo("_elif", [
        "elif ",
        _condicion(),
        ":",
        "\\n",
        "\\t",
        _codigo(),
        "\\n",
        Eleccion([
            Eleccion( [
                _else(), 
                _elif()
            ]),  
            "\\x"       
        ]),
        "\\n"
    ])
    
def _else():
    return Nodo("_else", [
        "else:", 
        "\\n", 
        "\\t", 
        codigo, 
        "\\n"
    ])
    
def _condicion():
    return Nodo("_condicion", [
        "(", 
        dato, 
        " ", 
        comparacion, 
        " ", 
        dato, 
        ")"
    ])
    
def _controlFunciones():
    return Nodo("_controlFunciones", [
        Eleccion(
            [
                _return(), 
                _yield()
            ])
    ])

def _return():
    return Nodo("_return" ,[
        "return ",
        Eleccion( [
            [
                "\\e", 
                [
                    _dato(), 
                    _llamadaFuncion()
                ]
            ], 
            "\\x"
        ]),       
        "\\n"
    ])

def _yield():
    return Nodo("_yield" ,[
        "yield ", 
        " ", 
        Eleccion( 
            [
                _dato(), 
                _llamadaFuncion()
            ]),       
        "\\n"
    ])
    
def _controlEstructural():
    return Nodo("_controlEstructural", [
        _try()
    ])
    
def _try():
    return Nodo("_try", [
        "try:",
        "\\n",
        "\\t",
        _codigo(),
        "\\n",
        "except",
        Eleccion([
            [" ", _palabra()],
            "\\x"
        ]),
        ":",
        "\\n",
        "\\t",
        _codigo(),
        "\\n",
        Eleccion(
            [
                _else(), 
                _finally(), 
                [_else(), _finally()]
            ]
        )          
    ])    

def _finally():
    return Nodo("_finally", [
        "finally:", 
        "\\n", 
        "\\t", 
        _codigo(), 
        "\\n"
    ])
    
def _with():
    return Nodo("_with", [
        "with open(",
        _directorio(),
        Eleccion([
            "r", 
            "w"
        ]),
        ") as ",
        _variable(),
        ":",
        "\\n",
        _codigo(),
    ])
    
def _declaracionEstructural():
    return Nodo("_declaracionEstructural", [
        Eleccion([
            _llamadaFuncion(), 
            _clase()
        ])        
    ])

def _argumentos():
    return Nodo("_argumentos", [
    [
        _argumento(), 
        Eleccion( [
            [
                ", ", 
                _argumentos()
            ],
            "\\x"
        ])]
    ])
    
def _argumento():
    return Nodo("_argumento", [
        _dato()
    ])
    
def _variablesClase():
    return Nodo([
        variable,
        Eleccion([
            _variablesClase(), 
            "\\x"
        ])        
    ])
    
def _funcionesClase():
    return Nodo([
        _funcion(), 
        Eleccion( [
            _funciones(), 
            "\\x"
        ])       
    ])
    
def _operacion():
    return Nodo([
        Eleccion([
            _operacionAritmetica(), 
            _operacionLogica(), 
            _operacionBitwise()
        ])        
    ])
    
def _operacionAritmetica():
    return Nodo([
        Eleccion([
            _suma(), 
            _resta(),
            _multiplicacion(), 
            _division(), 
            _modulo(),
            _potencia(), 
            _raiz()
        ])       
    ])
    
def _suma():
    return Nodo([
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ]),
        " ",
        _simboloSuma(),
        " ",
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ])        
    ])
    
def _resta():
    return Nodo([
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ]),
        " ",
        _simboloResta(),
        " ",
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ])
    ])
    
def _multiplicacion():
    return Nodo([
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ]), 
        " ",
        _simboloMultiplicacion(), 
        " ",
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ])
    ])
def _division():
    return Nodo([
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ]), 
        " ",
        _simboloDivision(), 
        " ",
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ])
    ])
    
def _modulo():
    return Nodo([
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ]), 
        " ",
        _simboloModulo(), 
        " ",
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ])
    ])
    
def _potencia():
    return Nodo([
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ]), 
        " ",
        _simboloPotencia(), 
        " ",
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ])
    ])
    
def _raiz():
    return Nodo([
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ]), 
        " ** (1 / ", 
        Eleccion([
            _variable(),
            __numero()(), 
            _funcion(), 
            _operacion()
        ]), 
        ")"
    ])
    
def _comparacion(): return Nodo("_comparacion", ["(", _dato(), " ", _simboloComparacion(), " ", _dato(), ")" ])
    
def _simboloSuma(): return Nodo("_simboloSuma", ["+"])

def _simboloResta(): return Nodo("_simboloResta", ["-"])

def _simboloMultiplicacion(): return Nodo("_simboloMultiplicacion", ["*"])

def _simboloDivision(): return Nodo("_simboloDivision", ["/"])

def _simboloModulo(): return Nodo("_simboloModulo", ["%"])

def _simboloPotencia(): return Nodo("_simboloPotencia", ["**"])

def _true(): return Nodo("_true", ["True"])

def _false(): return Nodo("_false", ["False"])

def _operacionBitwise(): 
    return Nodo("_operacionBitwise", [
        Eleccion( [
            _mascaraAnd(),
            _mascaraOr(),
            _mascaraNot(),
            _mascaraShiftIzquierda(),
            _mascaraShiftDerecha(),
        ])
    ])
    
def _mascaraAnd(): return Nodo("_mascaraAnd", [_dato(), " & ", _dato()])

def _mascaraOr(): return Nodo("_mascaraOr", [_dato(), "|", _dato()])

def _mascaraNot(): return Nodo("_mascaraNot", ["~", _dato()])

def _comentario():
    return Nodo("_comentario", [
        Eleccion( [
            _comentarioLinea(), 
            _comentarioBloque()
        ])       
    ])
    
def _comentarioLinea():
    return Nodo("_comentarioLinea", [
        "# ", 
        _contenidoComentario(), 
        "\\n"
    ])
    
def _comentarioBloque():
    return Nodo("_comentarioBloque", [
        "'''", 
        "\\n", 
        _contenidoComentario(), 
        "\\n", 
        "'''"
    ])
    
def _contenidoComentario():
    return Nodo("_contenidoComentario", [
        Eleccion( [
            "\\p", 
            textoLetras
        ]),
        Eleccion([
            _contenidoComentario(),
            "\\x"
        ])        
    ])
    
def _textoLetrasSimbolos():
    return Nodo("_textoLetrasSimbolos", [
        Eleccion([
            _letra(), 
            _simbolo()
        ]),
        Eleccion([
            _textoConSimbolos(), 
            "\\x"
        ])       
    ])
    
def _textoLetrasNumeros():
    return Nodo("_textoLetrasNumeros", [
        Eleccion( [
            _letra(), 
            _digito()
        ]),
        Eleccion([
            _textoLetrasNumeros(), 
            "\\x"
        ])        
    ])
    
def _textoLetras():
    return Nodo("_textoLetras", [
        _letra(), 
        Eleccion( [
            _textoLetras(), 
            "\\x"
        ])       
    ])
    
def _textos():
    return Nodo("_textos", [
        Eleccion([
            _textoLetras(),
            _textoLetrasNumeros(),
            _textoLetrasSimbolos(),
            _textoDirectorios(),
        ])        
    ])
    
def _variable():
    return Nodo("_variable", [
        _letra(), 
        _textoLetrasNumeros()
    ])
    
def _funciones():
    return Nodo("_funciones", [
        _funcion(), 
        "\\n", 
        Eleccion( [
            _funciones(), 
            "\\x"
        ]), 
        "\\n"
    ])
    
def _declaracionVariablesGlobales():
    return Nodo("_declaracionVariablesGlobales", [
        _variable(),
        "\\n",
        Eleccion( [
            _declaracionVariablesGlobales(), 
            "\\x"
        ]),
        "\\n"
    ])
    
def _codigo():
    return Nodo("_codigo", [
        Eleccion([
            _operacion(), 
            _asignacion(), 
            _control(), 
            _funcion(), 
            _comentario(), 
            _clase()
        ]),
        Eleccion( [
            _codigo(), 
            "\\x"
        ])
       
    ])
    
def _conjunto():
    return Nodo("_conjunto", [
        Eleccion([
            _lista(), 
            _tupla(), 
            _diccionario(), 
            _set()
        ])       
    ])
    
def _set():
    return Nodo("_set", [
        _variable(), 
        " = ", 
        "{", 
        _argumentos(), 
        "}"
    ])
def _diccionario():
    return Nodo("_diccionario", [
        _variable(), 
        " = ", 
        "{", 
        _argumentosKV(), 
        "}", 
        "\n"
    ])

def _argumentosKV():
    return Nodo("_argumentosKV", [
        _argumentoKV(),
        Eleccion([
            [", ", _argumentosKV()], 
            "\\x"
        ])       
    ])

def _argumentoKV():
    return Nodo("_argumentoKV", [
        _string(), 
        ": ",
        Eleccion([
            _dato(), 
            _funcion()
        ])       
    ])

def _tupla():
    return Nodo("_tupla", [
        "(", 
        _argumentos(), 
        ")", 
        "\\n"
    ])

def _lista():
    return Nodo("_lista", [
        "[", 
        _argumentos(), 
        "]", 
        "\\n"
    ])
    
def _bool():
    return Nodo("_bool", [
        Eleccion([
            _true(), 
            _false()
        ])        
    ])

def _string():
    return Nodo("_string", [
        '"', 
        _palabra(), 
        '"'
    ])

def _palabra():
    return Nodo("_palabra", [
        _char(), 
        Eleccion( [
            _palabra(), 
            "\\x"
        ])       
    ])
    
def _char():
    return Nodo("_char", [
        Eleccion( [
            _letra(), 
            _simbolo()
        ])       
    ])

def _letra():
    return Nodo("_letra", [
        Eleccion( [
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
            "Z"
        ])       
    ])

def _simbolo():
    return Nodo("_simbolo", [
        Eleccion([
            _simboloAritmetico(),
            _simboloLogico(),
            _simboloComparacion(),
            _parentesis(),
            _corchetes(),
            _llaves(),
            _comillas(),
        ])        
    ])
    
def _simboloAritmetico():
    return Nodo("_simboloAritmetico", [
        Eleccion([
            _simboloSuma(),
            _simboloResta(),
            _simboloMultiplicacion(),
            _simboloDivision(),
            _simboloModulo(),
            _simboloPotencia(),
        ])        
    ])

def _simboloLogico():
    return Nodo("_simboloLogico", [
        Eleccion([
            _and(), 
            _or(), 
            _not()
        ])       
    ])

def _and(): return Nodo("_and", ["and"])

def _or():  return Nodo("_or", ["or"])

def _not(): return Nodo("_not", ["not"])

def _simboloComparacion(): 
    return Nodo("", [
        Eleccion( [
            _equal(),
            _notEqual(),
            _greaterThan(),
            _lowerThan(),
            _greaterOrEqualThan(),
            _lowerOrEqualThan()
        ])       
    ])
    
def _equal(): return Nodo("_equal", ["=="]) 

def _notEqual(): return Nodo("_notEqual", ["!="]) 

def _greaterThan(): return Nodo("_greaterThan", [">"]) 

def _lowerThan(): return Nodo("_lowerThan", ["<"]) 

def _greaterOrEqualThan(): return Nodo("_greaterOrEqualThan", [">="]) 

def _lowerOrEqualThan(): return Nodo("_lowerOrEqualThan", ["<="]) 

def _parentesis(): 
    return Nodo("_parentesis", [
        Eleccion([
            "(", 
            ")"
        ])  
    ]) 

def _corchetes(): 
    return Nodo("_corchetes", [
        Eleccion([
            "[", 
            "]"
        ])         
    ]) 

def _llaves(): 
    return Nodo("_llaves", [
        Eleccion([
            "{", 
            "}"
        ])
    ]) 

def _comillas(): return Nodo("_comillas", ['"']) 

def __numero():
    return Nodo("__numero()", [
        Eleccion([
            _positivo(), 
            _negativo()
        ]),
        Eleccion([
            _integer(), 
            _double(), 
            _complex()
        ])        
    ])

def _integer():
    return Nodo("_integer", [
        _digito(), 
        Eleccion([
            _integer(), 
            "\\x"
        ])       
    ])

def _double():
    return Nodo("_double", [
        _integer(), 
        ".", 
        _integer()
    ])

def _complex():
    return Nodo("_complex", [
        "complex(",
        Eleccion([
            _positivo(), 
            _negativo()
        ]),
        Eleccion([
            _integer(), 
            _double()
        ]),
        ", ",
        Eleccion([
            _positivo(), 
            _negativo()
        ]),
        Eleccion([
            _integer(), 
            _double()
        ]),
        ")"
    ])

def _positivo(): return Nodo("_positivo", [""])

def _negativo(): return Nodo("_negativo", ["-"])

def _digito(): return Nodo("_digito", [Eleccion(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])])

def _dato():
    return Nodo("_dato", [
        Eleccion([
            _numero(),
            _string(),
            _bool(),
            _conjunto(),
            _variable(),
            _funcion(),
            _leerAtributoClase(),
            _llamadaFuncion(),
            _invocarMetodo()
        ])        
    ])

def _operacionLogica():
    return Nodo("_operacionLogica", [
        Eleccion([
            _operacionAnd(), 
            _operacionOr(), 
            _operacionNot(), 
            _comparacion(), 
            _true(), 
            _false()
        ])        
    ])

def _operacionAnd():
    return Nodo("_operacionAnd", [
        "(", 
        _comparacion(), 
        " ", 
        _and(), 
        " ", 
        _comparacion(), 
        ")"
    ])
    
def _operacionOr():
    return Nodo("_operacionOr", [
        "(", 
        _comparacion(), 
        " ", 
        _or(),
        " ", 
        _comparacion(), 
        ")"
    ])
    
def _operacionNot():
    return Nodo("_operacionNot", [
        _not(), 
        "(", 
        _comparacion(), 
        ")"
    ])

def _mascaraShiftIzquierda(): return Nodo("_mascaraShiftIzquierda", ["<<", _dato()]) 

def _mascaraShiftDerecha(): return Nodo("_mascaraShiftDerecha", [">>", _dato()]) 

def _forLista():
    return Nodo("_forLista", [
        "for ",
        _variable(),
        " in ",
        _variable(),
        ":",
        "\\n",
        "\\t",
        _codigoFuncion(),
        "\\n",
    ])

def _forIndice():
    return Nodo("_forIndice", [
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
    ])

def _forNumerico():
    return Nodo("_forNumerico", [
    "for ",
    _variable(),
    " in range(",
    Eleccion([
        [
            Eleccion([
                _integer(), 
                _variable(), 
                _llamadaFuncion()
            ])
        ],
        [
            Eleccion([
                _integer(), 
                _variable(), 
                _llamadaFuncion()
            ]),
            ", ",
            Eleccion([
                _integer(), 
                _variable(), 
                _llamadaFuncion()
            ])
        ],
        [
            Eleccion([
                _integer(), 
                _variable(), 
                _llamadaFuncion()
            ]),
            ", ",
            Eleccion([
                _integer(), 
                _variable(), 
                _llamadaFuncion()
            ]),
            ", ",
            Eleccion([
                _integer(), 
                _variable(), 
                _llamadaFuncion()
            ])
        ]
    ]),
    "):",
    "\\n",
    "\\t",
    _codigoBucle(),
    "\\n",
    Eleccion([
        _forElse(), 
        "\\x"
    ])    
])

def _forDict():
    return Nodo("_forDict", [
        "for ",
        _variable(),
        " in ",
        _variable(),
        ":",
        "\\n",
        "\\t",
        _codigoFuncion(),
        "\\n"
    ])
    
def _break(): return Nodo("_break", ["break ", "\\n"])

def _while():
    return Nodo("_while", [
        "while ",
        _condicion(),
        ":",
        "\\n",
        "\\t",
        _codigo(),
        "\\n",
        Eleccion( [
            ["\\n", _else()],
            "\\x"
        ]),       
        "\\n"
    ])

def _continue(): return Nodo("_continue", ["continue", "\\n"])

def _match(): 
    return Nodo("_match", [
        "match ",
        Eleccion([_variable(), _funcion()]),
        ":",
        "\\n",
        _cases(),
        Eleccion([
            ["case _:", "\\n", _codigo()], 
            "\\x"
        ])
    ])
    
def _cases():
    return Nodo("_cases", [
        "case ",
        _palabra(),
        ":",
        "\n",
        "\\t",
        _codigo(),
        "\\n",
        Eleccion([
            _cases(), 
            "\\x"
        ])
    ])
    
def _declaracionFuncion(): 
    return Nodo("_declaracionFuncion", [
        Eleccion([
                "declaracionFuncionNormal", 
                "declaracionFuncionMetodo",
        ]),
        "\\n"
    ])

def _declaracionFuncionNormal(): 
    return Nodo("_declaracionFuncionNormal", [
        "def ",
        "letra",
        "textoLetrasNumeros",
        "(",
        "argumentos",
        "):",
        "\\n",
        "\\t",
        Eleccion([
            [_pass()], 
            [_codigoFuncion()]
        ]),        
        "\\n"
    ])

def _declaracionFuncionAsincrona(): 
    return Nodo("_declaracionFuncionAsincrona", [
        "async def ",
        _letra(),
        _textoLetrasNumeros(),
        "(",
        _argumentos(),
        ")=",
        "\\n",
        "\\t",
        Eleccion([
            [_pass()], 
            [_codigoFuncionAsincrona()]
        ]),
        "\\n"
    ])

def _declaracionFuncionGeneradora(): 
    return Nodo("_declaracionFuncionGeneradora", [
        "def ",
        _letra()",
        _textoLetrasNumeros(),
        "(",
        _argumentos(),
        ")=",
        "\\n",
        "\\t",
        _codigoGenerador(),
        "\\n",
    ])

def _declaracionFuncionLambda():
    return Nodo("_declaracionFuncionLambda", [
        "lambda ",
        _argumentosLambda(),
        "= ",
        _expresionSimple(),
    ])

def _declaracionMetodo():
    return Nodo("_declaracionMetodo", [
        Eleccion([
            _declaracionMetodoNormal(),
            _declaracionMetodoAsincrono(),
            _declaracionMetodoEstatico(),
            _declaracionMetodoClase(),
        ]),
        Eleccion([
            _declaracionMetodo(), 
            "\\x"
        ])    
    ])

def _declaracionMetodoNormal(): 
    return Nodo("_declaracionMetodoNormal", [
        "def ",
        _letra(),
        _textoLetrasNumeros(),
        "(self",
        Eleccion([
            [", ", _argumentos()], 
            "\\x"
        ]),
        ")=",
        "\\n",
        "\\t",
        Eleccion([
            _pass(), 
            _codigoFuncion()
        ]),
        "\\n"
    ])

def _declaracionMetodoAsincrono(): 
    return Nodo("_declaracionMetodoAsincrono", [
        "async def ",
        _letra(),
        _textoLetrasNumeros(),
        "(self",
        Eleccion([
            [", ", _argumentos()], 
            "\\x"
        ]),
        ")=",
        "\\n",
        "\\t",
        Eleccion([
            _pass(), 
            _codigoFuncionAsincrona()
        ]),
        "\\n",
    ])
    
def _declaracionMetodoEstatico():
    return Nodo("_declaracionMetodoEstatico", [
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
        Eleccion([
            _pass(), 
            _codigoFuncion()
        ]),
        "\\n",
    ])
    
def _declaracionMetodoClase(): [
    "@classmethod",
    "\\n",
    "def ",
    "letra",
    "textoLetrasNumeros",
    "(cls",
    "\\e",
    [[", ", "argumentos"], "\\e"],
    ")=",
    "\\n",
    "\\e",
    [["\\t", "pass"], ["\\t", "codigoFuncion"]],
    "\\n",
],
"clase"= ["\\e", ["declaracionClase", "instanciacionClase", "usarClase"]],
"herencia"= ["letra", "textoLetrasNumeros", "\\e", [[", ", "herencia"], "\\e"]],
"metodosClase"= [
    "\\e",
    [["declaracionMetodo", "\\n", "\\t", "metodosClase"], "\\e"],
],
"constructorClase"= [
    "def __init__(self",
    "\\e",
    [[", ", "argumentos"], "\\e"],
    ")=",
    "\\n",
    "\\e",
    [["\\t", "pass"], ["\\t", "codigoFuncion"]],
    "\\n",
],
"atributosClase"= [
    "\\e",
    [["variable", " = ", "dato", "\\n", "atributosClase"], "\\e"],
],
"builtinOtrosUtilidad"= [
    "\\e",
    [
        ["len(", "argumentos", ")"],
        ["all(", "argumentos", ")"],
        ["any(", "argumentos", ")"],
        ["zip(", "argumentos", ")"],
        ["slice(", "argumentos", ")"],
        ["super(", "argumentos", ")"],
        ["object(", "argumentos", ")"],
        ["staticmethod(", "argumentos", ")"],
        ["classmethod(", "argumentos", ")"],
        ["property(", "argumentos", ")"],
    ],
],
"builtinOtrosEjecucion"= [
    "\\e",
    [
        ["eval(", "argumentos", ")"],
        ["exec(", "argumentos", ")"],
        ["compile(", "argumentos", ")"],
        ["__import__(", "argumentos", ")"],
    ],
],
"builtinOtros"= ["\\e", ["builtinOtrosUtilidad", "builtinOtrosEjecucion"]],
"builtinIOFichero"= [
    "\\e",
    [
        ["open(", "argumentos", ")"],
        ["read(", "argumentos", ")"],
        ["write(", "argumentos", ")"],
    ],
],
"builtinIOTexto"= [
    "\\e",
    [
        ["print(", "argumentos", ")"],
        ["input(", "argumentos", ")"],
        ["format(", "argumentos", ")"],
    ],
],
"builtinIO"= ["\\e", ["builtinIOTexto", "builtinIOFichero"]],
"builtinInspeccionAtributos"= [
    "\\e",
    [
        ["hasattr(", "argumentos", ")"],
        ["getattr(", "argumentos", ")"],
        ["setattr(", "argumentos", ")"],
        ["delattr(", "argumentos", ")"],
        ["dir(", "argumentos", ")"],
        ["vars(", "argumentos", ")"],
    ],
],
"builtinInspeccionTipos"= [
    "\\e",
    [
        ["type(", "argumentos", ")"],
        ["isinstance(", "argumentos", ")"],
        ["issubclass(", "argumentos", ")"],
        ["callable(", "argumentos", ")"],
    ],
],
"builtinInspeccion"= [
    "\\e",
    ["builtinInspeccionTipos", "builtinInspeccionAtributos"],
],
"builtinIteracionFuncional"= [
    "\\e",
    [
        ["map(", "argumentos", ")"],
        ["filter(", "argumentos", ")"],
        ["reduce(", "argumentos", ")"],
    ],
],
"builtinIteracionBasica"= [
    "\\e",
    [
        ["range(", "argumentos", ")"],
        ["enumerate(", "argumentos", ")"],
        ["zip(", "argumentos", ")"],
        ["reversed(", "argumentos", ")"],
        ["sorted(", "argumentos", ")"],
        ["iter(", "argumentos", ")"],
        ["next(", "argumentos", ")"],
    ],
],
"builtinIteracion"= [
    "\\e",
    ["builtinIteracionBasica", "builtinIteracionFuncional"],
],
"builtinMatematicasAvanzadas"= [
    "\\e",
    [["hash(", "argumentos", ")"], ["id(", "argumentos", ")"]],
],
"builtinMatematicasBasicas"= [
    "\\e",
    [
        ["abs(", "argumentos", ")"],
        ["round(", "argumentos", ")"],
        ["min(", "argumentos", ")"],
        ["max(", "argumentos", ")"],
        ["sum(", "argumentos", ")"],
        ["pow(", "argumentos", ")"],
        ["divmod(", "argumentos", ")"],
    ],
],
"builtinMatematicas"= [
    "\\e",
    ["builtinMatematicasBasicas", "builtinMatematicasAvanzadas"],
],
"builtinConversionTexto"= [
    "\\e",
    [
        ["str(", "argumentos", ")"],
        ["repr(", "argumentos", ")"],
        ["ascii(", "argumentos", ")"],
        ["chr(", "argumentos", ")"],
        ["ord(", "argumentos", ")"],
        ["hex(", "argumentos", ")"],
        ["oct(", "argumentos", ")"],
        ["bin(", "argumentos", ")"],
    ],
],
"builtinConversionSecuencia"= [
    "\\e",
    [
        ["list(", "argumentos", ")"],
        ["tuple(", "argumentos", ")"],
        ["set(", "argumentos", ")"],
        ["frozenset(", "argumentos", ")"],
        ["dict(", "argumentos", ")"],
        ["bytes(", "argumentos", ")"],
        ["bytearray(", "argumentos", ")"],
    ],
],
"builtinConversionNumerico"= [
    "\\e",
    [
        ["int(", "argumentos", ")"],
        ["float(", "argumentos", ")"],
        ["complex(", "argumentos", ")"],
        ["bool(", "argumentos", ")"],
    ],
],
"builtinConversion"= [
    "\\e",
    [
        "builtinConversionNumerico",
        "builtinConversionSecuencia",
        "builtinConversionTexto",
    ],
],
"builtinTipos"= [
    "\\e",
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
    ],
],
"builtin"= [
    "\\e",
    [
        "builtinTipos",
        "builtinConversion",
        "builtinMatematicas",
        "builtinIteracion",
        "builtinInspeccion",
        "builtinIO",
        "builtinOtros",
    ],
],
"declaracionClase"= [
    "class ",
    "letra",
    "textoLetrasNumeros",
    "\\e",
    [["(", "herencia", ")"], "\\e"],
    "=",
    "\\n",
    "\\t",
    "atributosClase",
    "\\n",
    "\\t",
    "constructor",
    "\\n",
    "\\t",
    "metodosClase",
    "\\n",
],
"instanciacionClase"= [
    "variable",
    " = ",
    "letra",
    "textoLetrasNumeros",
    "(",
    "\\e",
    [["argumentos"], "\\e"],
    ")",
],
"usoClase"= ["\\e", ["invocarMetodo", "atributoClase"]],
"encadenarMetodo"= [
    "variable",
    "(",
    "\\e",
    [["argumentos"], "\\e"],
    ")",
    "\\e",
    [[".", "encadenarMetodo"], "\\e"],
],
"atributoClase"= ["\\e", ["leerAtributoClase", "escribirAtributoClase"]],
"leerAtributoClase"= ["variable", ".", "variable"],
"escribirAtributoClase"= ["variable", ".", "variable", " = ", "dato"],
"raise"= ["raise", "\\e", [[" ", "\\e", ["llamadaFuncion", "variable"]], "\\e"]],
"ejecucion"= [
    "\\e",
    ["funcion", "clase", "builtin", "acessoFichero", "accesoInternet"],
],
"funcion"= ["\\e", ["declaracionFuncion", "llamadaFuncion"]],
"llamadaFuncion"= ["variable", "(", "\\e", [["argumentos"], "\\e"], ")"],
"invocarMetodo"= ["\\e", ["variable", "llamadaFuncion"], ".", "encadenarMetodo"],
"accesoRecurso"= ["accesoFichero", "accesoInternet"],
"accesoFichero"= [
    "\\e",
    ["leerFichero", "escribirFichero", "anadirFichero", "leerEscribirFichero"],
],
"leerFichero"= [
    "with open(",
    "textoDirectorioLocal",
    ", 'r') as ",
    "variable",
    "=",
    "\\n",
    "\\tcodigoFuncion",
],
"escribirFichero"= [
    "with open(",
    "textoDirectorioLocal",
    ", 'w') as ",
    "variable",
    "=",
    "\\n",
    "\\tcodigoFuncion",
],
"anadirFichero"= [
    "with open(",
    "textoDirectorioLocal",
    ", 'a') as ",
    "variable",
    "=",
    "\\n",
    "\\tcodigoFuncion",
],
"leerEscribirFichero"= [
    "with open(",
    "textoDirectorioLocal",
    ", 'r+') as ",
    "variable",
    "=",
    "\\n",
    "\\tcodigoFuncion",
],
"accesoInternet"= ["\\e", ["httpGet", "httpPost"]],
"httpGet"= ["requests.get(", "textoDirectorioWeb", ")"],
"httpPost"= ["requests.post(", "textoDirectorioWeb", ", data=", "dato", ")"],
"textoDirectorios"= ["\\e", ["textoDirectorioLocal", "textoDirectorioWeb"]],
"textoDirectorioLocal"= [
    "\\e",
    ["textoDirectorioWindows", "textoDirectorioLinux", "textoDirectorioMac"],
],
"textoDirectorioWindows"= [
    "\\e",
    ["letra", _digito(), "simboloDirectorioWindows"],
    "\\e",
    [["\\\\", "textoDirectorioWindows"], "\\e"],
]

def _textoDirectorioLinux():
    return Nodo("_textoDirectorioLinux", [
        Eleccion(["letra", _digito(), _simboloDirectorioLinux()]),
        Eleccion([["/", _textoDirectorioLinux()], "\\x"])
    ])

def _textoDirectorioMac()
    return Nodo("_textoDirectorioMac", [
        Eleccion([_letra(), _digito(), _simboloDirectorioMac()]),
        Eleccion([["/", _textoDirectorioMac()], "\\x"]),
    ])

def _textoDirectorioWeb(): return Nodo("_textoDirectorioWeb", [Eleccion([_urlWeb(), _urlLocal()])])

def _urlWeb():
    return Nodo("_urlWeb", [
        Eleccion(["http=//", "https=//"]),
        _textoDirectorioExterno(),
        Eleccion([[".", _textoDirectorioExterno()], "\\x"]),
        Eleccion([[".", _textoDirectorioExterno()], "\\x"]),
        Eleccion([["/", _directorioExternoRuta()], "\\x"]),
        Eleccion([["?", _directorioExternoParametros()], "\\x"])
    ])

def _textoDirectorioExterno():
    return Nodo("_textoDirectorioExterno", [
        Eleccion([
            _letra(), 
            _digito(), 
            _simboloDirectorioExterno()
        ]),
        Eleccion([
            _textoDirectorioExterno(), 
            "\\x"
        ])
    ])

def _simboloDirectorioExterno():
    return Nodo("_simboloDirectorioExterno", [
        Eleccion(["-", "_", ".", "~", "%", "+", "=", "&", "@", "!", "$", "'"])
    ])
        
def _directorioExternoRuta():
    return Nodo("_directorioExternoRuta", [
        _textoDirectorioExterno(),
        Eleccion([["/", _directorioExternoRuta()], "\\x"])
    ])

def _directorioExternoParametros():
    return Nodo("_directorioExternoParametros", [
        _textoDirectorioExterno(),
        "=",
        _textoDirectorioExterno(),
        Eleccion([["&", _directorioExternoParametros()], "\\x"])
    ])

def _urlLocal():
    return Nodo("_urlLocal", [
        Eleccion(["http=//", "https=//"]),        
        Eleccion(["localhost", "127.0.0.1", "0.0.0.0", "ipLocal"]),
        Eleccion([["=", _puerto()], "\\x"]),
        Eleccion([["/", _directorioExternoRuta()], "\\x"])        
    ])

def _ipLocal():
    return Nodo("_ipLocal", [
        _digito(),
        Eleccion([_digito(), "\\x"]),
        Eleccion([_digito(), "\\x"]),
        ".",
        _digito(),
        Eleccion([_digito(), "\\x"]),
        Eleccion([_digito(), "\\x"]),
        ".",
        _digito(),
        Eleccion([_digito(), "\\x"]),
        Eleccion([_digito(), "\\x"]),
        ".",
        _digito(),
        Eleccion([_digito(), "\\x"]),
        Eleccion([_digito(), "\\x"])  
    ])

def _puerto():
    return Nodo("_puerto", [
        _digito(),
        Eleccion([_digito(), "\\x"]),
        Eleccion([_digito(), "\\x"]),
        Eleccion([_digito(), "\\x"]),        
        Eleccion([_digito(), "\\x"])
    ])

guia = { 
    "programa": programa
}