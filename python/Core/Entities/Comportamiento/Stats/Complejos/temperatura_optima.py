# Core/Entities/Comportamiento/Stats/Complejos/temperatura_optima.py


from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Stats.stat_derivado import Stat_Derivado


class Temperatura_Optima(Stat_Derivado):
    def __init__(self, valores: list[Stat], **kwargs):

        super().__init__(nombre="temperatura_optima", valor=0, **kwargs)

    def calcular(self) -> float:
        # return self.valor_base - self._grasa.valor * 0.2
        raise NotImplementedError
