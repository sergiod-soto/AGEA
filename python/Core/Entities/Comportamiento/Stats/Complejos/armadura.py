from Core.Entities.Comportamiento.Stats.Complejos.stat_complejo import Stat_Complejo


class Armadura(Stat_Complejo):
    """ """

    def __init__(self, valor_Armadura, **kwargs):
        super().__init__(**kwargs)
        self.valor_Armadura = valor_Armadura

