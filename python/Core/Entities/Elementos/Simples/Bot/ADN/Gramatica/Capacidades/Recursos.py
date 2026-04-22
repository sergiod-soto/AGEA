from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.Elementos import Nodo


def _accesoRecurso():
    return Nodo(
        "_accesoRecurso",
        [
            Nodo.Eleccion(
                [
                    _accesoFichero,
                    _accesoInternet,
                ]
            )
        ],
    )


def _accesoFichero():
    return Nodo(
        "_accesoFichero",
        [
            Nodo.Eleccion(
                [
                    _leerFichero,
                    _escribirFichero,
                    _anadirFichero,
                    _leerEscribirFichero,
                ]
            )
        ],
    )


def _leerFichero():
    from Base_Gramatica import _variable, _codigoFuncion

    return Nodo(
        "_leerFichero",
        [
            "with open(",
            _textoDirectorioLocal,
            ", 'r') as ",
            _variable,
            ":\n",
            Nodo.Tab(_codigoFuncion),
            "\n",
        ],
    )


def _escribirFichero():
    from Base_Gramatica import _variable, _codigoFuncion

    return Nodo(
        "_escribirFichero",
        [
            "with open(",
            _textoDirectorioLocal,
            ", 'w') as ",
            _variable,
            ":\n",
            Nodo.Tab(_codigoFuncion),
            "\n",
        ],
    )


def _anadirFichero():
    from Base_Gramatica import _variable, _codigoFuncion

    return Nodo(
        "_anadirFichero",
        [
            "with open(",
            _textoDirectorioLocal,
            ", 'a') as ",
            _variable,
            ":\n",
            Nodo.Tab(_codigoFuncion),
            "\n",
        ],
    )


def _leerEscribirFichero():
    from Base_Gramatica import _variable, _codigoFuncion

    return Nodo(
        "_leerEscribirFichero",
        [
            "with open(",
            _textoDirectorioLocal,
            ", 'r+') as ",
            _variable,
            ":\n",
            Nodo.Tab(_codigoFuncion),
            "\n",
        ],
    )


def _accesoInternet():
    return Nodo("_accesoInternet", [Nodo.Eleccion([_httpGet, _httpPost])])


def _httpGet():
    return Nodo("_httpGet", ["requests.get(", _textoDirectorioWeb, ")"])


def _httpPost():
    from Base_Gramatica import _dato

    return Nodo(
        "_httpPost", ["requests.post(", _textoDirectorioWeb, ", data=", _dato, ")"]
    )


def _textoDirectorios():
    return Nodo(
        "_textoDirectorios",
        [Nodo.Eleccion([_textoDirectorioLocal, _textoDirectorioWeb])],
    )


def _textoDirectorioLocal():
    return Nodo(
        "_textoDirectorioLocal",
        [
            Nodo.Eleccion(
                [
                    _textoDirectorioWindows,
                    _textoDirectorioLinux,
                    _textoDirectorioMac,
                ]
            )
        ],
    )


def _textoDirectorioWindows():
    from Base_Gramatica import _letra, _digito, _stop

    return Nodo(
        "_textoDirectorioWindows",
        [
            Nodo.Eleccion([_letra, _digito, _simboloDirectorioWindows]),
            Nodo.Eleccion([["\\\\", _textoDirectorioWindows], _stop]),
        ],
    )


def _textoDirectorioLinux():
    from Base_Gramatica import _letra, _digito, _stop

    return Nodo(
        "_textoDirectorioLinux",
        [
            Nodo.Eleccion([_letra, _digito, _simboloDirectorioLinux]),
            Nodo.Eleccion([["/", _textoDirectorioLinux], _stop]),
        ],
    )


def _textoDirectorioMac():
    from Base_Gramatica import _letra, _digito, _stop

    return Nodo(
        "_textoDirectorioMac",
        [
            Nodo.Eleccion([_letra, _digito, _simboloDirectorioMac]),
            Nodo.Eleccion([["/", _textoDirectorioMac], _stop]),
        ],
    )


def _simboloDirectorioWindows():
    return Nodo(
        "_simboloDirectorioWindows",
        [
            Nodo.Eleccion(
                [
                    Nodo.Eleccion(
                        [
                            " ",
                            "!",
                            "#",
                            "$",
                            "%",
                            "&",
                            "'",
                            "(",
                            ")",
                            "+",
                            ",",
                            "-",
                        ]
                    ),
                    Nodo.Eleccion(
                        [
                            ".",
                            ";",
                            "=",
                            "@",
                            "[",
                            "]",
                            "^",
                            "_",
                            "`",
                            "{",
                            "}",
                            "~",
                        ]
                    ),
                ]
            )
        ],
    )


def _simboloDirectorioLinux():
    return Nodo(
        "_simboloDirectorioLinux",
        [
            Nodo.Eleccion(
                [
                    Nodo.Eleccion(
                        [
                            " ",
                            "!",
                            '"',
                            "#",
                            "$",
                            "%",
                            "&",
                            "'",
                            "(",
                            ")",
                            "*",
                            "+",
                            ",",
                            "-",
                            ".",
                        ]
                    ),
                    Nodo.Eleccion(
                        [
                            "/",
                            ":",
                            ";",
                            "<",
                            "=",
                            ">",
                            "?",
                            "@",
                            "[",
                            "\\",
                            "]",
                            "^",
                            "_",
                            "`",
                            "{",
                            "|",
                            "}",
                            "~",
                        ]
                    ),
                ]
            )
        ],
    )


def _simboloDirectorioMac():
    return Nodo(
        "_simboloDirectorioMac",
        [
            Nodo.Eleccion(
                [
                    Nodo.Eleccion(
                        [
                            " ",
                            "!",
                            '"',
                            "#",
                            "$",
                            "%",
                            "&",
                            "'",
                            "(",
                            ")",
                            "*",
                            "+",
                            ",",
                            "-",
                            ".",
                        ]
                    ),
                    Nodo.Eleccion(
                        [
                            "/",
                            ":",
                            ";",
                            "<",
                            "=",
                            ">",
                            "?",
                            "@",
                            "[",
                            "\\",
                            "]",
                            "^",
                            "_",
                            "`",
                            "{",
                            "|",
                            "}",
                            "~",
                        ]
                    ),
                ]
            )
        ],
    )


def _textoDirectorioWeb():
    return Nodo("_textoDirectorioWeb", [Nodo.Eleccion([_urlWeb, _urlLocal])])


def _urlWeb():
    from Base_Gramatica import _stop

    return Nodo(
        "_urlWeb",
        [
            Nodo.Eleccion(["http://", "https://"]),
            _textoDirectorioExterno,
            Nodo.Eleccion([[".", _textoDirectorioExterno], _stop]),
            Nodo.Eleccion([[".", _textoDirectorioExterno], _stop]),
            Nodo.Eleccion([["/", _directorioExternoRuta], _stop]),
            Nodo.Eleccion([["?", _directorioExternoParametros], _stop]),
        ],
    )


def _textoDirectorioExterno():
    from Base_Gramatica import _letra, _digito, _stop

    return Nodo(
        "_textoDirectorioExterno",
        [
            Nodo.Eleccion([_letra, _digito, _simboloDirectorioExterno]),
            Nodo.Eleccion([_textoDirectorioExterno, _stop]),
        ],
    )


def _simboloDirectorioExterno():
    return Nodo(
        "_simboloDirectorioExterno",
        [
            Nodo.Eleccion(
                [
                    "-",
                    "_",
                    ".",
                    "~",
                    "%",
                    "+",
                    "=",
                    "&",
                    "@",
                    "!",
                    "$",
                    "'",
                ],
            )
        ],
    )


def _directorioExternoRuta():
    from Base_Gramatica import _stop

    return Nodo(
        "_directorioExternoRuta",
        [
            _textoDirectorioExterno,
            Nodo.Eleccion([["/", _directorioExternoRuta], _stop]),
        ],
    )


def _directorioExternoParametros():
    from Base_Gramatica import _stop

    return Nodo(
        "_directorioExternoParametros",
        [
            _textoDirectorioExterno,
            "=",
            _textoDirectorioExterno,
            Nodo.Eleccion([["&", _directorioExternoParametros], _stop]),
        ],
    )


def _urlLocal():
    from Base_Gramatica import _stop

    return Nodo(
        "_urlLocal",
        [
            Nodo.Eleccion(["http://", "https://"]),
            Nodo.Eleccion(["localhost", "127.0.0.1", "0.0.0.0", _ipLocal]),
            Nodo.Eleccion([[":", _puerto], _stop]),
            Nodo.Eleccion([["/", _directorioExternoRuta], _stop]),
        ],
    )


def _ipLocal():
    from Base_Gramatica import _digito, _stop

    return Nodo(
        "_ipLocal",
        [
            _digito,
            Nodo.Eleccion([_digito, _stop]),
            Nodo.Eleccion([_digito, _stop]),
            ".",
            _digito,
            Nodo.Eleccion([_digito, _stop]),
            Nodo.Eleccion([_digito, _stop]),
            ".",
            _digito,
            Nodo.Eleccion([_digito, _stop]),
            Nodo.Eleccion([_digito, _stop]),
            ".",
            _digito,
            Nodo.Eleccion([_digito, _stop]),
            Nodo.Eleccion([_digito, _stop]),
        ],
    )


def _puerto():
    from Base_Gramatica import _digito, _stop

    return Nodo(
        "_puerto",
        [
            _digito,
            Nodo.Eleccion([_digito, _stop]),
            Nodo.Eleccion([_digito, _stop]),
            Nodo.Eleccion([_digito, _stop]),
            Nodo.Eleccion([_digito, _stop]),
        ],
    )
