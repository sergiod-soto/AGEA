from Core.Entities.Comportamiento.comportamiento import Comportamiento as C
from Core.Entities.Elementos.Simples.Comida.comida import Comida

comportamientos = C.declarar_comportamientos()


class Fruta(Comida):
    def __init__(self, tipo, casilla, capa):
        super().__init__(tipo, casilla, capa)
