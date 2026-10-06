# Core/Entities/Mundo/Suelo/suelo_arena.py

from Core.Entities.Comportamiento.Terreno.terreno_arenoso import Arenoso
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Arena(Suelo, Arenoso):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Arena,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=65,
            inercia_termica=1.3e6,
        )
