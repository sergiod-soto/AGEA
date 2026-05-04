from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento

"""
un elemento es Combinable si puede ser dividido en 2 elementos iguales de inferior cantidad
"""


class Combinable(Material):
    def __init__(self, elemento: Elemento, cantidad_max: float = None):
        super().__init__()
        self.elemento = elemento
        self.cantidad_max = cantidad_max or float("inf")

    @abstractmethod
    def combinar(self, elemento: Elemento) -> bool: ...
