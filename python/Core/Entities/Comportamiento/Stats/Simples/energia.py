# Core/Entities/Comportamiento/Stats/Simples/energia.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Energia(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="energia", valor=valor)
