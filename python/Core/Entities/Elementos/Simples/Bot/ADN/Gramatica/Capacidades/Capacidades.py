from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.elementos import Nodo
from Core.Entities.Elementos.Simples.Bot.ADN.Gramatica.Capacidades.acceso_recurso import _accesoRecurso


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