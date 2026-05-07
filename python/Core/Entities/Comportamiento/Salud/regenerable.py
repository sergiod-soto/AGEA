from abc import abstractmethod

from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Temporal.temporal import Temporal


class Regenerable(Temporal):
    """
    Indica que el Elemento tiene stats que regeneran con el tiempo

    Parametros:

    - tasas_regeneracion: list[tuple[Stat, float]]

    Metodos abstractos:

    - tick()
    """

    def __init__(self, tasas_regeneracion: list[tuple[Stat, float]], **kwargs):
        super().__init__(**kwargs)
        self.tasas_regeneracion = tasas_regeneracion

    @abstractmethod
    def tick(self): ...
