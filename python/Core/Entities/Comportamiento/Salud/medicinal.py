# Core/Entities/Comportamiento/Salud/medicinal.py

from abc import abstractmethod

from Core.Entities.Comportamiento.Salud.salud import Salud


class Medicinal(Salud):
    """
    Recupera salud si se ingiere

    Parametros:

    - valor_medicinal: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"valor_medicinal: float"}
    ABSTRACTOS = {}

    def __init__(self, valor_medicinal: float, **kwargs):
        super().__init__(**kwargs)
        self.valor_medicinal = valor_medicinal

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"medicinal": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"medicinal": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "valor_medicinal",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Si es consumido por un Elemento con el atributo Salud, verá esta regenerada.

Atributos:
\valor_medicinal: float,

Métodos:
\t-
        """
