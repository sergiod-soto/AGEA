from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class Terreno_Arenoso(Terreno):

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
