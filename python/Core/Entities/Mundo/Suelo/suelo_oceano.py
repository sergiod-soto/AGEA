# Core/Entities/Mundo/Suelo/suelo_oceano.py

from Core.Entities.Comportamiento.Terreno.terreno_oceano import Oceanico
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Oceano(Suelo, Oceanico):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Oceano,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=92,
            inercia_termica=2.2e7,
        )
