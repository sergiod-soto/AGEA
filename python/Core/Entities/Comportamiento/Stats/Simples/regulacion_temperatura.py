# Core/Entities/Comportamiento/Stats/Simples/regulacion_temperatura.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Regulacion_Temperatura(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="regulacion_temperatura", valor=valor)
