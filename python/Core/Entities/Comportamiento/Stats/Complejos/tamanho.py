from Core.Entities.Comportamiento.Stats.Complejos.stat_complejo import Stat_Complejo


class Tamanho(Stat_Complejo):
    """ """

    def __init__(self, valor_Tamanho, **kwargs):
        super().__init__(**kwargs)
        self.valor_Tamanho = valor_Tamanho

