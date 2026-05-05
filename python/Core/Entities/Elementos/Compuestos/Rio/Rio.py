from Core.Entities.Elementos.Compuestos.elemento_compuesto import Elemento_Compuesto
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C

comportamientos = C.declarar_comportamientos()


class Rio(Elemento_Compuesto):

    def __init__(self):
        super().__init__(capa=-1)
