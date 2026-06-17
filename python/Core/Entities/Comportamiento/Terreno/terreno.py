from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.meta import RestriccionMeta


class Terreno(Comportamiento):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
