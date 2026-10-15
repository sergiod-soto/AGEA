# Core/Entities/Comportamiento/Interaccion/interaccion.py

from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Interaccion(Comportamiento):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
