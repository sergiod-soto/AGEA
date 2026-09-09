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

    REQUIERE = {"cantidad_minima_divisible: float"}
    ABSTRACTOS = {"def dividir(self, cantidad: float) -> Elemento | None"}

    def __init__(self, cantidad_minima_divisible: float, **kwargs):
        super().__init__(**kwargs)
        self.cantidad_minima_divisible = cantidad_minima_divisible

    @abstractmethod
    def dividir(self, cantidad: float) -> Elemento | None: ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "cantidad_minima_divisible",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser dividido en otros, 
con las mismas características pero menor cantidad.

Atributos:
\tcantidad_minima_divisible: float

Métodos:
\t@abstractmethod dividir(self, cantidad: float) -> Elemento | None
\t--------------------------------------
\tDivide el elemento en 'cantidad' y resto, es caso de ser posible.
        """
