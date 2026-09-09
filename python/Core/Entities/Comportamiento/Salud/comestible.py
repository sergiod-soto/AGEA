from abc import abstractmethod

from Core.Entities.Comportamiento.Salud.salud import Salud
from Core.Entities.Elementos.elemento import Elemento


class Comestible(Salud):
    """
    Se puede ingerir

    Parametros:

    -

    Metodos abstractos:

    - comer(self, por: Elemento)
    """

    REQUIERE = {}
    ABSTRACTOS = {"def comer(self, por: Elemento)"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def comer(self, por: Elemento): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "peso",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Puede ser asimilado (comido).

Atributos:
\t-

Métodos:
\t@abstractmethod comer(self, por: Elemento)
\t--------------------------------------
\tEl efecto que produce al Elemento ser asimilado.
        """
