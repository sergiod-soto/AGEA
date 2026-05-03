from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion


class Destruible(Interaccion):
    def __init__(self, durabilidad_max: float, durabilidad_actual: float = None):
        super().__init__()
        self.durabilidad_max = durabilidad_max
        self.durabilidad_actual = durabilidad_actual or durabilidad_max

    @abstractmethod
    def danhar(self, danho: float): ...

    @abstractmethod
    def restaurar(self, danho: float): ...
    
    @abstractmethod
    def destruir(self, danho: float): ...   