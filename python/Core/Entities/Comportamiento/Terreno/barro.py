from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class Barro(Terreno):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)