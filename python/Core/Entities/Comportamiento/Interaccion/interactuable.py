from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Interactuable(Interaccion):
    """
    Metodos abstractos:

    - interaccion(self, por:Elemento)
    """

    def __init__(self,**kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def interaccion(self, por: Elemento): ...
