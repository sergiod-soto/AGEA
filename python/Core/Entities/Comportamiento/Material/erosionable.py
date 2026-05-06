from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Erosionable(Material):
    """
    Parametros:

    - condiciones: list[tuple[list[Condicion], float]]

    - durabilidad_max: float

    - durabilidad_actual: float = None

    Metodos abstractos:

    - erosionar(self, cantidad: float)

    - _destruir(self, efecto: Accion)
    """

    def __init__(
        self,
        condiciones_erosion: list[tuple[list[Condicion], float]],
        durabilidad_max_erosion: float,
        durabilidad_actual_erosion: float = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.durabilidad_max_erosion = durabilidad_max_erosion
        self.condiciones_erosion = condiciones_erosion
        self.durabilidad_actual_erosion = durabilidad_actual_erosion or durabilidad_max_erosion

    def tick(self) -> None:
        super().tick()
        for condiciones, cantidad in self.condiciones_erosion:
            if all(c.evaluar() for c in condiciones):
                self.erosionar(cantidad)

    @abstractmethod
    def erosionar(self, cantidad: float): ...

    @abstractmethod
    def _destruir(self, efecto: Accion): ...
