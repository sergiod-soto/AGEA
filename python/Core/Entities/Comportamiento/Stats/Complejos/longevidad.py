from Core.Entities.Comportamiento.Stats.Complejos.stat_complejo import Stat_Complejo


class Longevidad(Stat_Complejo):
    """ """

    def __init__(self, valor_Longevidad, **kwargs):
        super().__init__(**kwargs)
        self.valor_Longevidad = valor_Longevidad
