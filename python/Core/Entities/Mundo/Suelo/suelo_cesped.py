# Core/Entities/Mundo/Suelo/suelo_cesped.py

from Core.Entities.Comportamiento.Terreno.herboso import Hervoso
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Cesped(Suelo, Hervoso):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Cesped,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=75,
            inercia_termica=3e5,
        )
    def tick_elemento(self, ctx): ...