from Core.Entities.Comportamiento.Salud.salud import Salud


class Nutritivo(Salud):
    """
    Recupera energia si se ingiere

    Parametros:

    - valor_nutritivo: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"valor_nutritivo: float"}
    ABSTRACTOS = {}

    def __init__(self, valor_nutritivo: float, **kwargs):
        super().__init__(**kwargs)
        self.valor_nutritivo = valor_nutritivo

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "valor_nutritivo",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Si un Elemento con Nutricion lo consume, verá esta regenerada.

Atributos:
\tvalor_nutritivo: float,

Métodos:
\t-
        """
