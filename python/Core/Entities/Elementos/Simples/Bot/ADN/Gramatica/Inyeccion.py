

from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.elementos import Nodo


def _importsHardCoded():
    return Nodo(
        "_importsBasicos",
        [
            #
            # _Tipos y estructuras________________________________________
            Nodo.Import("functools", ["reduce"]),
            Nodo.Import(
                "collections",
                ["defaultdict", "Counter", "deque", "OrderedDict", "namedtuple"],
            ),
            Nodo.Import(
                "itertools", ["chain", "combinations", "permutations", "product"]
            ),
            "\n",
            #
            # _Strings y texto____________________________________________
            Nodo.Import(None, ["string"]),
            "\n",
            #
            # _Sistema básico_____________________________________________
            Nodo.Import(None, ["os"]),
            Nodo.Import(None, ["sys"]),
            Nodo.Import(None, ["math"]),
            Nodo.Import(None, ["time"]),
            Nodo.Import(None, ["copy"]),
            Nodo.Import(None, ["json"]),
            "\n",
            #
            # _Utilidades de código_______________________________________
            Nodo.Import(
                "typing", ["List", "Dict", "Tuple", "Optional", "Any", "Union"]
            ),
            "\n",
            #
            # _Estructuras adicionales____________________________________
            Nodo.Import("functools", ["wraps", "partial", "lru_cache"]),
            "\n",
            #
            # _Números____________________________________________________
            Nodo.Import(None, ["statistics"]),
            "\n",
            #
            # _Control del programa_______________________________________
            Nodo.Import(None, ["warnings"]),
            Nodo.Import("abc", ["ABC", "abstractmethod"]),
            "\n",
            #
            # _Inspección básica__________________________________________
            Nodo.Import(None, ["inspect"]),
            Nodo.Import("enum", ["Enum", "auto"]),
            #
            #
            # ____________________________________________________________
            # Nodo.Import(None, None),
            # ____________________________________________________________
            #
            #
        ],
    )


def _codigoInyectado():
    """
    Codigo escrito 100% a mano.
    No puede depender de nada contenido en Base_Gramatica.py

    Se ejecuta despues de _importsHardCoded y antes de _funciones
    """

    return Nodo(
        "_codigoInyectado",
        [
            "",
        ],
    )
