from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.Elementos import Nodo
from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.Capacidades.Recursos import _accesoRecurso


def _capacidad():
    return Nodo(
        "_capacidad",
        [
            Nodo.Eleccion(
                [
                    _accesoRecurso,
                ]
            )
        ],
    )