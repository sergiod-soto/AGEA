# Core/Entities/Comportamiento/Stats/Simples/edad_adulta.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Edad_Adulta(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="edad_adulta", valor=valor)
