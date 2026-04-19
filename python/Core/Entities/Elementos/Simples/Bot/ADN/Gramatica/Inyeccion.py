from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.Elementos import Nodo





def _importsHardCoded():
    return Nodo(
        "_importsBasicos",
        [
            "from functools import reduce\n",
            "",
            "",
        ],
    )
    
def _codigoInyectado():
    return Nodo("_codigoInyectado", [""])
