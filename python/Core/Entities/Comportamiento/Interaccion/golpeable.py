from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Golpeable(Material):
    """
    Metodos abstractos:

    golpear(self, por: Elemento)
    """

    def __init__(self):
        super().__init__()
        self.golpeable = True

    @abstractmethod
    def golpear(self, por: Elemento): ...
