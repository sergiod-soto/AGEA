# Core/Entities/Comportamiento/Energetico/energetico.py

from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Energetico(Comportamiento):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    