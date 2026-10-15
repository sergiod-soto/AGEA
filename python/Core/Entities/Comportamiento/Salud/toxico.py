# Core/Entities/Comportamiento/Salud/toxico.py

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

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"toxico": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"toxico": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

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
