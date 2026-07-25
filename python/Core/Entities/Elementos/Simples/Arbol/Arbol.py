from Core.Entities.Comportamiento.comportamiento import Comportamiento as C
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple

comportamientos = C.declarar_comportamientos()

# los arboles no se pueden mover. generan comida y semillas periodicamente
# las semillas se convierten en arbol despues de un tiempo si no hay mas de una cierta
# cantidad de arboles alrededor y hay agua
#
# las semillas se dispersan en un area alrededor del arbol en funcion del viento


class Arbol(Elemento_Simple, comportamientos):

    def __init__(
        self,
        id,
        tamanho,
        casilla,
        **kwargs,
    ):
        super().__init__(
            Arbol,
            id,
            tamanho,
            casilla,
            1,
            **kwargs,
        )

    def crear_fruto(self) -> None: ...

    def tick() -> None: ...
