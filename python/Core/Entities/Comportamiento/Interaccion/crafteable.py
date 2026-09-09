from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.Abstractos.Recetas.receta import Receta


class Crafteable(Interaccion):
    """
    Parametros:

    - receta: Receta

    Metodos abstractos:

    -
    """

    REQUIERE = {"receta: Receta"}
    ABSTRACTOS = {}

    def __init__(self, receta: Receta, **kwargs):
        super().__init__(**kwargs)
        self.receta = receta

        for ingrediente in self.receta.ingredientes:
            ingrediente.incluir_en_receta(self.receta)

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "peso",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser generado siguiendo una receta.

Atributos:
\treceta: Receta

Métodos:
\t-
        """
