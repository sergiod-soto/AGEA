# Core/Entities/Comportamiento/Stats/Simples/vida.py


from Core.Entities.Comportamiento.Stats.stat import Stat


class Vida(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="vida", valor=valor)
