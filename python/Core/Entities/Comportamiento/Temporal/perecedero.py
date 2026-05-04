from abc import abstractmethod

from Core.Entities.Comportamiento.Temporal.temporal import Temporal
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Perecedero(Temporal):
    """Durabilidad decae con el tiempo a un ritmo diferente segun condiciones"""

    def __init__(
        self,
        tiempo_maximo_perecedero: float,
        condiciones: list[tuple[list[Condicion], float]],
        tiempo_actual_perecedero: float = None,
    ):
        super().__init__()
        self.tiempo_maximo_perecedero = tiempo_maximo_perecedero
        self.tiempo_actual_perecedero = (
            tiempo_actual_perecedero or tiempo_maximo_perecedero
        )
        self.condiciones = condiciones

        @abstractmethod
        def tick(self) -> None: ...

        @abstractmethod
        def desaparecer(self) -> None: ...
