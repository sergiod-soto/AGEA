from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Liquido(Material):
    """
    Parametros:

    -

    Metodos abstractos:

    -
    """

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, disuelto: list[Elemento] = None, **kwargs):
        super().__init__(**kwargs)
        self.disuelto = disuelto or []

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Indica que el Elemento es Liquido.

Atributos:
\t-

Métodos:
\t-
        """
