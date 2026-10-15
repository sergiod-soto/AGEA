# Core/Entities/Comportamiento/Stats/Modificadores/modificador.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Modificador(Stat):
    def __init__(self, nombre: str, valor, **kwargs):
        super().__init__(nombre, valor, **kwargs)
