from abc import abstractmethod

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C


comportamientos = C.declarar_comportamientos(

)

class Condicion(Elemento_Abstracto):

    def __init__(self):
        super().__init__(Condicion)
    
    @abstractmethod
    def evaluar(self, contexto: dict) -> bool: ...