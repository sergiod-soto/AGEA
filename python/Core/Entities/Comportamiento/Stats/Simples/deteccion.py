# Core/Entities/Comportamiento/Stats/Simples/deteccion.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Deteccion(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="deteccion", valor=valor)
