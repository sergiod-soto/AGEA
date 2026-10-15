# Core/Entities/Comportamiento/Material/divisible.py

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

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"divisible": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"divisible": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

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
