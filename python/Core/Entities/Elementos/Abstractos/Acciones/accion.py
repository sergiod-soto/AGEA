from abc import abstractmethod

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C


class Accion(Elemento_Abstracto):

    def __init__(self):
        super().__init__(Accion)

    @abstractmethod
    def ejecutar(self): ...
