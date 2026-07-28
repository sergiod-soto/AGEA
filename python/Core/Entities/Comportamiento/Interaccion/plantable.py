from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Plantable(Interaccion):
    """
    Parametros:

    -

    Metodos abstractos:

    - plantar(self, agujero: Elemento)
    - desplantar(self, por: Elemento)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plantado = False

    @classmethod
    def _campos_internos(cls):
        return {"plantado"}

    @abstractmethod
    def plantar(self, agujero: Elemento): ...

    @abstractmethod
    def desplantar(self, por: Elemento): ...
