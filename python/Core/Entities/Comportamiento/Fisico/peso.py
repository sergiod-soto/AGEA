from Core.Entities.Comportamiento.Fisico.fisico import Fisico

"""
NO indica que algo pese mucho, si no que tiene masa
"""


class Peso(Fisico):

    def __init__(self, masa: float):
        super().__init__()
        self.masa = masa
