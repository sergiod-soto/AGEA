from Core.Entities.Elementos.Complejos.elemento_complejo import Elemento_Complejo
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C

comportamientos = C.declarar_comportamientos()


class Oceano(Elemento_Complejo):

    def __init__(self):
        self.tiene_dentro = None
