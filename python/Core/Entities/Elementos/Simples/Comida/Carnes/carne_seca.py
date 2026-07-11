from Core.Entities.Elementos.Simples.Comida.Carnes.carne import Carne
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C

comportamientos = C.declarar_comportamientos()


class Carne_Seca(Carne):
    def __init__(self, casilla, capa):
        super().__init__(Carne_Seca, casilla, capa)
