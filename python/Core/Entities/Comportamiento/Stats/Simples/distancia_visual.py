# Core/Entities/Comportamiento/Stats/Simples/distancia_visual.py

from numpy import uint64

from Core.Entities.Comportamiento.Stats.stat import Stat


class Distancia_Visual(Stat):
    def __init__(self, valor: uint64):
        # TODO: formula que acepte la distancia maxima del mundo
        # y el valor y retorne la distancia maxima para ese bot
        super().__init__(
            nombre="distancia_visual",
            valor=valor,
        )
