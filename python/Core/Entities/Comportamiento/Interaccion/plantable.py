from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Plantable(Interaccion):
    """
    Parametros:

    - plantado: bool = False

    Metodos abstractos:

    - plantar(self, agujero: Elemento)
    - desplantar(self, por: Elemento)
    """

    def __init__(self, plantado: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.plantado = plantado

    @abstractmethod
    def plantar(self, agujero: Elemento): ...

    @abstractmethod
    def desplantar(self, por: Elemento): ...
