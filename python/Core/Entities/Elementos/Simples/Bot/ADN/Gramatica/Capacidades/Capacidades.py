from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.elementos import Nodo
from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.Capacidades.acceso_recurso import (
    _accesoRecurso,
)
from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.Capacidades.API_Mundo.api_mundo import _api_mundo



def _capacidad():
    return Nodo(
        "_capacidad",
        [
            Nodo.Eleccion(
                [
                    _general,
                    # _api_mundo,
                ]
            )
        ],
    )


def _general():
    return Nodo(
        "_general",
        [
            Nodo.Eleccion(
                [
                    _accesoRecurso,
                ]
            )
        ],
    )



