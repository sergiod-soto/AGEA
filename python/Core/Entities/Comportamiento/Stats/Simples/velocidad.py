# Core/Entities/Comportamiento/Stats/Simples/velocidad.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Velocidad(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="velocidad", valor=valor)
