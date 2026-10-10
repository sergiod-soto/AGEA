from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion


class Destruible(Interaccion):
    """
    Solo se interactua dañandolo o restaurandolo.

    Al llegar la durabilidad a 0, es cuando se destruye.

    - ------------------------------------------------------

    Parametros:

    - durabilidad_max_destruible: float
    - durabilidad_actual_destruible: float = None

    Metodos abstractos:

    - danhar(self, danho: float)
    - restaurar(self, danho: float)
    - _destruir(self, danho: float)
    """

    REQUIERE = {"durabilidad_max_destruible: float"}
    ABSTRACTOS = {
        "def danhar(self, danho: float)",
        "def restaurar(self, danho: float)",
        "def _destruir(self, danho: float)",
    }

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"destruible": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"destruible": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    def __init__(self, durabilidad_max_destruible: float, **kwargs):
        super().__init__(**kwargs)
        self.durabilidad_max_destruible = durabilidad_max_destruible
        self.durabilidad_actual_destruible = durabilidad_max_destruible

    @classmethod
    def _campos_internos(cls):
        return {"durabilidad_actual_destruible"}

    @abstractmethod
    def danhar(self, danho: float): ...

    @abstractmethod
    def restaurar(self, danho: float): ...

    @abstractmethod
    def _destruir(self, danho: float): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "durabilidad_max_destruible",
            "durabilidad_actual_destruible",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser destruido como consecuencia de una acción directa.

Atributos:
\tdurabilidad_max_destruible: float

Métodos:
\t@abstractmethod danhar(self, danho: float)
\t--------------------------------------
\tConsume carga de energía.

\t@abstractmethod restaurar(self, danho: float)
\t--------------------------------------
\tRecarga energía.

\t@abstractmethod _destruir(self, danho: float)
\t--------------------------------------
\tRecarga energía.
            """
