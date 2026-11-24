from Core.Entities.Comportamiento.comportamiento import Comportamiento as C
from Core.Entities.Elementos.Complejos.elemento_complejo import Elemento_Complejo

comportamientos = C.declarar_comportamientos()


class Rio(Elemento_Complejo):

    def __init__(self):
        super().__init__(capa=-1)
