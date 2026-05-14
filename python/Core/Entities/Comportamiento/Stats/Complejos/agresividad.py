from Core.Entities.Comportamiento.Stats.Complejos.stat_complejo import Stat_Complejo


class Agresividad(Stat_Complejo):
    """ """

    def __init__(self, valor_Agresividad, **kwargs):
        super().__init__(**kwargs)
        self.valor_Agresividad = valor_Agresividad
