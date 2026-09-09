from Core.Entities.Comportamiento.Salud.salud import Salud


class Toxico(Salud):
    """
    Reduce salud si se ingiere

    Parametros:

    - valor_toxico: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"valor_toxico: float"}
    ABSTRACTOS = {}

    def __init__(self, valor_toxico: float, **kwargs):
        super().__init__(**kwargs)
        self.valor_toxico = valor_toxico

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "peso",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Si un ser con Vida lo consume, ve esta reducida.

Atributos:
\tvalor_toxico: float

Métodos:
\t-
        """
