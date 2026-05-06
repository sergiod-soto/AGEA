from Core.Entities.Comportamiento.Fisico.fisico import Fisico

"""
NO indica que algo pese mucho, si no que tiene masa

Parametros:

- masa: float
"""


class Peso(Fisico):

    def __init__(self, peso: float, **kwargs):
        super().__init__(**kwargs)
        self.peso = peso
