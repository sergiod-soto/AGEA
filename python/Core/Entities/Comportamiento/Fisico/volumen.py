from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Volumen(Fisico):
    """
    (cm3)

    Parametros:

    - volumen: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"volumen: float"}
    ABSTRACTOS = {}

    def __init__(self, volumen: float, **kwargs):
        super().__init__(**kwargs)
        self.volumen = volumen

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "volumen",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento tiene volumen espacial.

Atributos:
\tvolumen: float

Métodos:
\t-
        """

    def representar_volumen(self) -> list[str]:
        """
        Informacion pasada a Unity para representar el Elemento
        """
        representacion = {"volumen": {"volumen": self.volumen}}
        return representacion
