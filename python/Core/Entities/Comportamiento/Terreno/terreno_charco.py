from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class Charco(Terreno):

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
