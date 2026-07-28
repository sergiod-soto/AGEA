from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Recolectable(Interaccion):
    """
    Indica si puede ser recolectardo para obtener Elemento(s)

    Parametros:

    - contenido_recolectable: dict[str, tuple[Elemento, float]] = None

    Metodos abstractos:

    - recolectar(self, por: Elemento)
    """

    def __init__(
        self, contenido_recolectable: dict[str, tuple[Elemento, float]] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.contenido_recolectable = contenido_recolectable or {}

 

    @abstractmethod
    def recolectar(self, por: Elemento): ...
