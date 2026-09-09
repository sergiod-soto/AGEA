from Core.Entities.Comportamiento.Social.social import Social


class Intercambiable(Social):
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
        return [
            "",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
TODO: terminar
•El Elemento puede ser transferido de uno a otro Bot.

Atributos:
\t-

Métodos:
\tgastar(self, cantidad: float) -> float
\t--------------------------------------
\tConsume carga de energía.


\tcargar(self, cantidad: float)
\t--------------------------------------
\tRecarga energía.
            """