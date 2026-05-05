from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Recolectable(Interaccion):
    """
    Indica si puede ser recolectardo para obtener Elemento(s)

    Metodos abstractos:

    recolectar(self, por: Elemento)
    """

    def __init__(self, contenido: dict[str, tuple[Elemento, float]] = None):
        super().__init__()
        self.contenido = contenido or {}

    @abstractmethod
    def recolectar(self, por: Elemento): ...
