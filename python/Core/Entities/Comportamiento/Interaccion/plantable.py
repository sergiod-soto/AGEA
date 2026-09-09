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

    REQUIERE = {}
    ABSTRACTOS = {
        "def plantar(self, agujero: Elemento)",
        "def desplantar(self, por: Elemento)",
    }

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

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Indica si el Elemento tiene algún efecto especial al ser enterrado.

Atributos:
\t-

Métodos:
\t@abstractmethod plantar(self, agujero: Elemento)
\t--------------------------------------
\tSe entierra.


\t@abstractmethod desplantar(self, por: Elemento)
\t--------------------------------------
\tSe desentierra.
        """
