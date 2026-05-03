from abc import abstractmethod

from Core.Entities.Comportamiento.Informativo.informativo import Informativo


class Sonoro(Informativo):
    """
    Ejemplo de uso:
    Las pisadas de un bot, no el bot en si
    """

    def __init__(self, intensidad: float, sonido):
        super().__init__()
        self.intensidad = intensidad
        self.sonido = sonido

    @abstractmethod
    def sonar(self): ...
