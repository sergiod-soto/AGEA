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
