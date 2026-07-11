from Core.Entities.Elementos.Simples.Comida.comida import Comida
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C

comportamientos = C.declarar_comportamientos()


class Carne(Comida):

    def __init__(self, tipo, casilla, capa):
        super().__init__(tipo, casilla, capa)
