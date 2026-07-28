from Core.Entities.Comportamiento.Stats.Complejos.stat_complejo import Stat_Complejo


class Temperatura_Optima(Stat_Complejo):
    """ """

    def __init__(self, valor_Temperatura_Optima, **kwargs):
        super().__init__(**kwargs)
        self.valor_Temperatura_Optima = valor_Temperatura_Optima

