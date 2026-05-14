from Core.Entities.Comportamiento.Stats.Complejos.stat_complejo import Stat_Complejo


class Percepcion(Stat_Complejo):
    """ """

    def __init__(self, valor_Percepcion, **kwargs):
        super().__init__(**kwargs)
        self.valor_Percepcion = valor_Percepcion
