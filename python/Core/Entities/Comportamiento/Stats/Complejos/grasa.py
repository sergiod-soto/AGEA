from Core.Entities.Comportamiento.Stats.Complejos.stat_complejo import Stat_Complejo


class Grasa(Stat_Complejo):
    """ """

    def __init__(self, valor_Grasa, **kwargs):
        super().__init__(**kwargs)
        self.valor_Grasa = valor_Grasa

