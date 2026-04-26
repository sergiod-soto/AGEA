from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.elementos import Nodo


def _importsHardCoded():
    return Nodo(
        "_importsBasicos",
        [
            #
            # Tipos y estructuras
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
            # Strings y texto
            Nodo.Import(None, ["string"]),
            "\n",
            #
            # Sistema básico
            Nodo.Import(None, ["os"]),
            Nodo.Import(None, ["sys"]),
            Nodo.Import(None, ["math"]),
            Nodo.Import(None, ["time"]),
            Nodo.Import(None, ["copy"]),
            Nodo.Import(None, ["json"]),
            "\n",
            #
            # Utilidades de código
            Nodo.Import(
                "typing", ["List", "Dict", "Tuple", "Optional", "Any", "Union"]
            ),
            "\n",
            #
            # Estructuras adicionales
            Nodo.Import("functools", ["wraps", "partial", "lru_cache"]),
            "\n",
            #
            # Números
            Nodo.Import(None, ["statistics"]),
            "\n",
            #
            # Control del programa
            Nodo.Import(None, ["warnings"]),
            Nodo.Import("abc", ["ABC", "abstractmethod"]),
            "\n",
            #
            # Inspección básica
            Nodo.Import(None, ["inspect"]),
            Nodo.Import("enum", ["Enum", "auto"]),
            #
            #
            #######################################################
            Nodo.Import(None, None),
            #######################################################
            #
            #
        ],
    )


def _codigoInyectado():
    '''
        Codigo escrito 100% a mano. 
        No puede depender de nada contenido en Base_Gramatica.py
        
        Se ejecuta despues de _importsHardCoded y antes de _funciones
    '''
    
    return Nodo("_codigoInyectado", [""])
