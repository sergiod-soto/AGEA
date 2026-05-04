from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Divisible(Material):
    def __init__(self, cantidad_minima: float):
        super().__init__()
        self.cantidad_minima = cantidad_minima

    @abstractmethod
    def dividir(self, cantidad: float) -> Elemento | None: ...
