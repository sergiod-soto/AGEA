from Core.Entities.Elementos.Abstractos.Marcadores.Espaciales.marcador_espacial import (
    Marcador_Espacial,
)
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C

comportamientos = C.declarar_comportamientos()


class Agujero(Marcador_Espacial):
    def __init__(self, **kwargs):
        super().__init__(Agujero, **kwargs)
