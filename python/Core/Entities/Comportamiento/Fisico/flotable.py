from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Flotable(Fisico):
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
        return """
•El Elemento mantiene capa > 0 en terreno de agua.

Atributos:
\t-

Métodos:
\t-
        """
