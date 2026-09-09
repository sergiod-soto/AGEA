from abc import abstractmethod

from Core.Entities.Comportamiento.Salud.salud import Salud


class Medicinal(Salud):
    """
    Recupera salud si se ingiere

    Parametros:

    - valor_medicinal: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"valor_medicinal: float"}
    ABSTRACTOS = {}

    def __init__(self, valor_medicinal: float, **kwargs):
        super().__init__(**kwargs)
        self.valor_medicinal = valor_medicinal

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "valor_medicinal",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Si es consumido por un Elemento con el atributo Salud, verá esta regenerada.

Atributos:
\valor_medicinal: float,

Métodos:
\t-
        """
