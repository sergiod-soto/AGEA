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

    def __init__(self, humedad_max: float, **kwargs):
        super().__init__(**kwargs)
        self.humedad_max = humedad_max
        self.humedad_actual: float = humedad_max

    @abstractmethod
    def humedecer(self, cantidad):
        pass

    @abstractmethod
    def secar(self, cantidad):
        pass
