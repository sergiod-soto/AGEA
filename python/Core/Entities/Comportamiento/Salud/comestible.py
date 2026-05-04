from abc import abstractmethod

from Core.Entities.Comportamiento.Salud.salud import Salud
from Core.Entities.Elementos.elemento import Elemento


class Comestible(Salud):
    """Se puede ingerir"""

    def __init__(self):
        super().__init__()

    @abstractmethod
    def comer(self, por: Elemento): ...
