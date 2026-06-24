from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Terreno(Comportamiento):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
