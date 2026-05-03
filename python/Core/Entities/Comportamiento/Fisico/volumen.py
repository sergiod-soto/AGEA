from Core.Entities.Comportamiento.Fisico.fisico import Fisico

"""
NO indica que algo pese mucho, si no que tiene masa
"""


class Volumen(Fisico):

    def __init__(self, volumen: float):
        super().__init__()
        self.volumen = volumen
