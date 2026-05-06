from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Divisible(Material):
    """
    Lo mismo que combinable pero al reves

    Parametros:

    - cantidad_minima: float

    Metodos abstractos:

    - dividir(self, cantidad: float) -> Elemento | None
    """

    def __init__(self, cantidad_minima: float,**kwargs):
        super().__init__(**kwargs)
        self.cantidad_minima = cantidad_minima

    @abstractmethod
    def dividir(self, cantidad: float) -> Elemento | None: ...
