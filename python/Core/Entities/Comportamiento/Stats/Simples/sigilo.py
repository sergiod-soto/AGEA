# Core/Entities/Comportamiento/Stats/Simples/sigilo.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Sigilo(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="sigilo", valor=valor)
