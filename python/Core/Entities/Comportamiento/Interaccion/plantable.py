from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Plantable(Interaccion):
    def __init__(self, plantado: bool = False, plantable: bool = True):
        super().__init__()
        self.plantado = plantado
        self.plantable = plantable

    @abstractmethod
    def plantar(self, agujero: Elemento): ...

    @abstractmethod
    def desplantar(self, por: Elemento): ...
