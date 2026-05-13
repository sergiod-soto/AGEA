from Core.Entities.Comportamiento.Interaccion.ingrediente import Ingrediente
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.Simples.Agua.agua import Agua
from Core.Entities.Elementos.Simples.Comidas.Ingredientes.harina import Harina
from Core.Entities.Elementos.Simples.Comidas.Ingredientes.ingrediente import (
    Ingrediente as Elemento_Ingrediente,
)

comportamientos = Comportamiento.declarar_comportamientos(
    Ingrediente,
)


# TODO: definir Masa_Pan
class Masa_Pan(Elemento_Ingrediente, comportamientos):
    def __init__(self, agua: Agua, harina: Harina):
        super().__init__(
            recetas_de=None,
        )
