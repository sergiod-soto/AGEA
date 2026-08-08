# Core/Entities/Comportamiento/Stats/Simples/energia.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Ataque(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="ataque", valor=valor)
