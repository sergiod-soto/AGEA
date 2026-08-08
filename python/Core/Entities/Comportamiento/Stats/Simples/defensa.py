# Core/Entities/Comportamiento/Stats/Simples/defensa.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Defensa(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="defensa", valor=valor)
