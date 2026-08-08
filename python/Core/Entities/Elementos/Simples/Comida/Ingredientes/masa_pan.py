from Core.Entities.Comportamiento.Interaccion.ingrediente import Ingrediente
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.Simples.Agua.agua import Agua
from Core.Entities.Elementos.Simples.Comida.Ingredientes.harina import Harina

comportamientos = Comportamiento.declarar_comportamientos()


# TODO: definir Masa_Pan
class Masa_Pan(comportamientos):
    def __init__(self, casilla, capa):
        super().__init__(Masa_Pan, casilla, capa)
