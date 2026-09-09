from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Interactuable(Interaccion):
    """
    Parametros:

    -

    Metodos abstractos:

    - interaccion(self, por:Elemento)
    """

    REQUIERE = {}
    ABSTRACTOS = {"def interaccion(self, por: Elemento)"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def interaccion(self, por: Elemento): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser interactuado (un botón, una palanca...).

Atributos:
\t-

Métodos:
\t@abstractmethod interaccion(self, por: Elemento)
\t--------------------------------------
\tInteractua.
        """
