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

    REQUIERE = {"contenido_recolectable: dict[str, tuple[Elemento, float]] = None"}
    ABSTRACTOS = {"def recolectar(self, por: Elemento)"}

    def __init__(
        self, contenido_recolectable: dict[str, tuple[Elemento, float]] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.contenido_recolectable = contenido_recolectable or {}

    @abstractmethod
    def recolectar(self, por: Elemento): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser recolectado para la generacion de otro Elemento.

Atributos:
\tcontenido_recolectable: dict[str, tuple[Elemento, float]] = None

Métodos:
\t@abstractmethod recolectar(self, por: Elemento)
\t--------------------------------------
\tProvoca la generacion del recurso, si posible.
        """
