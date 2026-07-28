from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Divisible(Material):
    """
    Lo mismo que combinable pero al reves

    Parametros:

    - cantidad_minima_divisible: float

    Metodos abstractos:

    - dividir(self, cantidad: float) -> Elemento | None
    """

    def __init__(self, cantidad_minima_divisible: float, **kwargs):
        super().__init__(**kwargs)
        self.cantidad_minima_divisible = cantidad_minima_divisible

    
    @abstractmethod
    def dividir(self, cantidad: float) -> Elemento | None: ...
