from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion


class Destruible(Interaccion):
    """
    Solo se interactua dañandolo o restaurandolo.

    Al llegar la durabilidad a 0, es cuando se destruye.

    - ------------------------------------------------------

    Parametros:

    - durabilidad_max: float
    - durabilidad_actual: float = None

    Metodos abstractos:

    - danhar(self, danho: float)
    - restaurar(self, danho: float)
    - _destruir(self, danho: float)
    """

    def __init__(
        self, durabilidad_max: float, durabilidad_actual: float = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.durabilidad_max = durabilidad_max
        self.durabilidad_actual = durabilidad_actual or durabilidad_max

    @abstractmethod
    def danhar(self, danho: float): ...

    @abstractmethod
    def restaurar(self, danho: float): ...

    @abstractmethod
    def _destruir(self, danho: float): ...
