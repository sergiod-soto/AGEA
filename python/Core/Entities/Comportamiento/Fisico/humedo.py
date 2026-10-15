# Core/Entities/Comportamiento/Fisico/flotable.py

from abc import abstractmethod

from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Humedo(Fisico):
    """
    Parametros:

    - humedad_max: float

    Metodos abstractos:

    - humedecer(self, cantidad)
    - secar(self, cantidad)
    """

    REQUIERE = {"humedad_max: float"}
    ABSTRACTOS = {}

    def __init__(self, humedad_max: float, **kwargs):
        super().__init__(**kwargs)
        self.humedad_max = humedad_max
        self.humedad_actual: float = humedad_max

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"humedo": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"humedo": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def _campos_internos(cls):
        return {
            "humedad_actual",
        }

    @abstractmethod
    def humedecer(self, cantidad):
        pass

    @abstractmethod
    def secar(self, cantidad):
        pass

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "peso",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
TODO
            """
