from abc import abstractmethod
import random
from typing import Callable

from Core.Entities.Comportamiento.Informativo.informativo import Informativo


class Sonoro(Informativo):
    """
    Ejemplo de uso de clase:

    Las pisadas de un bot, no el bot en si

    Parametros:

    -

    Metodos abstractos:

    - sonar(self, intensidad: float))

     ------------------------------------

    Ejemplo de implementacion:

    def sonar(self):\n
    ____timbre = Sonoro.generar_timbre(\n
    ________fundamental=lambda: 2000 / (self.masa ** (1/3)),\n
    ________n_armonicos=4,\n
    ________decay=0.6,\n
    ________inarmonicidad=0.0,\n
    ____)\n
    ____# hacer algo con el timbre...
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
