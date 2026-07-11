from Core.Entities.Elementos.Abstractos.Marcadores.marcador import Marcador
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C


comportamientos = C.declarar_comportamientos(

)

class Rastro(Marcador):
    def __init__(self,**kwargs):
        super().__init__(Rastro, **kwargs)
