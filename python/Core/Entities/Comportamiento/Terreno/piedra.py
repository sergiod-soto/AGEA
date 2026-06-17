from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class Piedra(Terreno):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)