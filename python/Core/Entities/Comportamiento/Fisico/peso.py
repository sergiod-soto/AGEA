# Core/Entities/Comportamiento/Fisico/peso.py

from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Peso(Fisico):
    """
    (kilos.gramos)

    NO indica que algo pese mucho, si no que tiene masa

    Parametros:

    - peso: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"peso: float"}
    ABSTRACTOS = {}

    def __init__(self, peso: float, **kwargs):
        super().__init__(**kwargs)
        self.peso = peso

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "peso",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Peso es la masa del elemento.

Atributos:
\tpeso: float

Métodos:
\t-
            """
