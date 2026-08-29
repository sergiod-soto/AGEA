from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class Gravoso(Terreno):

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
