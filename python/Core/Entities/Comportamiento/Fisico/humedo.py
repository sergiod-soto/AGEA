from abc import abstractmethod

from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Humedo(Fisico):

    def __init__(self, humedad_max: float):
        super().__init__()
        self.humedad_max = humedad_max
        self.humedad_actual = humedad_max

    @abstractmethod
    def humedecer(self, cantidad):
        pass

    @abstractmethod
    def secar(self, cantidad):
        pass


