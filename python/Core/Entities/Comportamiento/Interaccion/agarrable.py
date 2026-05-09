from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Agarrable(Interaccion):
    """
    Forma en la que un Elemento puede ser desplazado por otro de forma directa, sin "empujar"

    Parametros:

    - agarrado_por: Elemento

    Metodos abstractos:

    - agarrar(self, por: Elemento)

    - soltar(self, por: Elemento)
    """

    def __init__(self, agarrado_por: Elemento = None, **kwargs):
        super().__init__(**kwargs)
        self.agarrado_por = agarrado_por

    @abstractmethod
    def agarrar(self, por: Elemento):
        """Accion pasiva. Se indica que el elemento atributo tiene intencion de agarrar este elemento"""
        ...

    @abstractmethod
    def soltar(self, por: Elemento):
        """Accion pasiva. Se indica que el elemento atributo tiene intencion de soltar este elemento"""
        ...
