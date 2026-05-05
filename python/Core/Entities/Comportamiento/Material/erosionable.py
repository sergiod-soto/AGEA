from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Erosionable(Material):
    """
    Parametros:

    condiciones: list[tuple[list[Condicion], float]]

    durabilidad_max: float

    durabilidad_actual: float = None

    Metodos abstractos:

    erosionar(self, cantidad: float)

    _destruir(self, efecto: Accion)
    """

    def __init__(
        self,
        condiciones: list[tuple[list[Condicion], float]],
        durabilidad_max: float,
        durabilidad_actual: float = None,
    ):
        super().__init__()
        self.durabilidad_max = durabilidad_max
        self.condiciones = condiciones
        self.durabilidad_actual = durabilidad_actual or durabilidad_max

    def tick(self) -> None:
        super().tick()
        for condiciones, cantidad in self.condiciones:
            if all(c.evaluar() for c in condiciones):
                self.erosionar(cantidad)

    @abstractmethod
    def erosionar(self, cantidad: float): ...

    @abstractmethod
    def _destruir(self, efecto: Accion): ...
