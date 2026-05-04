from abc import abstractmethod

from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Temporal.temporal import Temporal


class Regenerable(Temporal):
    def __init__(
        self,
        tasas_regeneracion: list[tuple[Stat, float]],
    ):
        super().__init__()
        self.tasas_regeneracion = tasas_regeneracion

    @abstractmethod
    def tick(self): ...
