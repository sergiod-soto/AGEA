from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class Arena(Terreno):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
