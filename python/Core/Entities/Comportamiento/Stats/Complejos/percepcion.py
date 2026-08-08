# Core/Entities/Comportamiento/Stats/Complejos/percepcion.py

from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Stats.stat_derivado import Stat_Derivado


class Percepcion(Stat_Derivado):
    """ """

    def __init__(self, valores: list[Stat], **kwargs):
        super().__init__(nombre="percepcion", valor = 0, **kwargs)

    def calcular(self) -> float:
        raise NotImplementedError