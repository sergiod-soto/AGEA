# Core/Entities/Comportamiento/Salud/salud.py

from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Salud(Comportamiento):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
