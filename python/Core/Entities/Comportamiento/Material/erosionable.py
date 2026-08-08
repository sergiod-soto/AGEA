from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Erosionable(Material):
    """
    Parametros:

    - condiciones_erosion: list[tuple[list[Condicion], float]]
    - durabilidad_max_erosion: float
    - durabilidad_actual_erosion: float = None

    Metodos abstractos:

    - erosionar(self, cantidad: float)
    - _destruir(self, efecto: Accion)
    """

    REQUIERE = {
        "condiciones_erosion: list[tuple[list[Condicion], float]]",
        "durabilidad_max_erosion: float",
    }
    ABSTRACTOS = {
        "def erosionar(self, cantidad: float)",
        "def _destruir(self, efecto: Accion)",
    }

    def __init__(
        self,
        durabilidad_max_erosion: float,
        condiciones_erosion: list[tuple[list[Condicion], float]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.durabilidad_max_erosion = durabilidad_max_erosion
        self.condiciones_erosion = condiciones_erosion
        self.durabilidad_actual_erosion = durabilidad_max_erosion

    @classmethod
    def _campos_internos(cls):
        return {"durabilidad_actual_erosion"}

    def tick(self) -> None:
        # TODO: comporbar que funciona correctamente y no machaca ningun otro tick()
        super().tick()
        for condiciones, cantidad in self.condiciones_erosion:
            if all(c.evaluar() for c in condiciones):
                self.erosionar(cantidad)

    @abstractmethod
    def erosionar(self, cantidad: float): ...

    @abstractmethod
    def _destruir(self, efecto: Accion): ...
