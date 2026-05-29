from abc import abstractmethod
from enum import Enum
import random
from typing import Callable

from Core.Entities.Comportamiento.Informativo.informativo import Informativo


class Sonoro(Informativo):
    """
    Parametros:

    - sonidos: dict[str, list[Callable[[], float]]]

    Metodos abstractos:

    - sonar(self, intensidad: float))

    ------------------------------------
    Ejemplo de implementacion:

    def sonar(self):
    - timbre = Sonoro.generar_timbre(
        - fundamental=lambda: 2000 / (self.masa ** (1/3)),
        - n_armonicos=4,
        - decay=0.6,
        - inarmonicidad=0.0,
    - )
    - #hacer algo con el timbre (...)
    """

    def __init__(self, sonidos: dict[str, list[Callable[[], float]]], **kwargs):
        self.sonidos = sonidos
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
    def sonar(self, intensidad: float, sonido):
        """
        Se encarga de hacer sonar en el mundo un sonido
        previamente elegido con una determinada intensidad.
        """
        ...
