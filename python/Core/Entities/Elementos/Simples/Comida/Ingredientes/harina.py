from Core.Entities.Comportamiento.Interaccion.ingrediente import Ingrediente
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.Simples.Comida.Ingredientes.ingrediente import (
    Ingrediente as Elemento_Ingrediente,
)

comportamientos = Comportamiento.declarar_comportamientos(
    Ingrediente,
)


# TODO: definir harina
class Harina(Elemento_Ingrediente, comportamientos):
    def __init__(self, tipo, casilla, capa):
        super().__init__(Harina, casilla, capa)
