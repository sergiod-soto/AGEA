from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Golpeable(Material):
    """
    Parametros:

    -

    Metodos abstractos:

    - golpear(self, por: Elemento)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.golpeable = True

    @classmethod
    def _campos_internos(cls):
        return {"golpeable"}

    @abstractmethod
    def golpear(self, por: Elemento): ...
