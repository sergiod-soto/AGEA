# Core/Entities/Comportamiento/Stats/Simples/edad.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Edad(Stat):
    def __init__(self, valor: int, edad_adulta: int):
        super().__init__(nombre="edad", valor=valor)
        self.edad_adulta = edad_adulta
