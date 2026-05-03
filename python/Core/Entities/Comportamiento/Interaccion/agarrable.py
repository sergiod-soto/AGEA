from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Agarrable(Interaccion):
    def __init__(self, agarrado_por: Elemento):
        super().__init__()
        self.agarrado_por = agarrado_por

    @abstractmethod
    def agarrar(self, por: Elemento):
        """Accion pasiva. Se indica que el elemento atributo tiene intencion de agarrar este elemento"""
        ...

    @abstractmethod
    def soltar(self, por: Elemento):
        """Accion pasiva. Se indica que el elemento atributo tiene intencion de soltar este elemento"""
        ...
