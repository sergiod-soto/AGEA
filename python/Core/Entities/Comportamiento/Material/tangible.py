from Core.Entities.Comportamiento.Material.material import Material


class Tangible(Material):
    """
    Parametros:

    -

    Metodos abstractos:

    -
    """

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Indica que el Elemento es tangible.

Atributos:
\t-

Métodos:
\t-
        """
