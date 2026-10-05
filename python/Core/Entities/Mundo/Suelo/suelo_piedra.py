# Core/Entities/Mundo/Suelo/suelo_piedra.py

from Core.Entities.Comportamiento.Terreno.terreno_rocoso import Rocoso
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Piedra(Suelo, Rocoso):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Piedra,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=75,
            inercia_termica=4e5,
        )

    def tick(self, pos, ctx): ...
