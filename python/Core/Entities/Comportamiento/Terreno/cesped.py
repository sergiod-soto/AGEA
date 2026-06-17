from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class Cesped(Terreno):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)