# Core/Entities/Comportamiento/Stats/Simples/temperatura.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Temperatura(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="temperatura", valor=valor)
