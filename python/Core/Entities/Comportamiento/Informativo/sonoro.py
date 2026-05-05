from abc import abstractmethod
import random
from typing import Callable

from Core.Entities.Comportamiento.Informativo.informativo import Informativo


class Sonoro(Informativo):
    """
    Ejemplo de uso de clase:\n
    Las pisadas de un bot, no el bot en si

    Metodos abstractos:

    - sonar(self, intensidad: float))\n

    ------------------------------------\n
    Ejemplo de implementacion:

    def sonar(self):
        timbre = Sonoro.generar_timbre(
            fundamental=lambda: 2000 / (self.masa ** (1/3)),
            n_armonicos=4,
            decay=0.6,
            inarmonicidad=0.0,
        )
        # hacer algo con el timbre...
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def generar_timbre(
        fundamental: Callable[[], float],
        n_armonicos: int,
        decay: float,
        inarmonicidad: float,
    ) -> list[tuple[float, float]]:
        return [
            (
                fundamental()
                * (i + 1)
                * (1 + inarmonicidad * i * random.gauss(0, 0.05)),
                decay**i,
            )
            for i in range(n_armonicos)
        ]

    @abstractmethod
    def sonar(self, intensidad: float): ...
