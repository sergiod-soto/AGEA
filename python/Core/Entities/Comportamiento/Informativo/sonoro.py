from abc import abstractmethod
from enum import Enum
import random
from typing import Callable

from Core.Entities.Comportamiento.Informativo.informativo import Informativo


class Sonoro(Informativo):
    """
    Parametros:

    - sonidos

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
    - hacer algo con el timbre...
    """

    def __init__(self, sonidos: list[tuple[str, list[tuple[float, float]]]], **kwargs):
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
    def sonar(self, intensidad: float, sonido): ...


class Libreria_Sonidos:
    """
    clase biblioteca para ordenar los sonidos
    """

    class Piedra:
        def Golpear(masa):
            return Sonoro.generar_timbre(
                fundamental=lambda: 2000 / (masa ** (1 / 3)),
                n_armonicos=4,
                decay=0.6,
                inarmonicidad=0.0,
            )

        def Rodar(masa):
            return Sonoro.generar_timbre(
                fundamental=lambda: 2000 / (masa ** (1 / 3)),
                n_armonicos=4,
                decay=0.6,
                inarmonicidad=0.0,
            )

    class Agua: ...
