from Core.Entities.Comportamiento.Stats.Complejos.stat_complejo import Stat_Complejo


class Movilidad(Stat_Complejo):
    """ """

    def __init__(self, valor_Movilidad, **kwargs):
        super().__init__(**kwargs)
        self.valor_Movilidad = valor_Movilidad

