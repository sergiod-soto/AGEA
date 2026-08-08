from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class Grava(Terreno):

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
