# Core/Entities/Mundo/Suelo/suelo_agua.py

from Core.Entities.Comportamiento.Terreno.acuoso import Acuoso
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Agua(Suelo, Acuoso):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Agua,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=92,
            inercia_termica=2.1e7,
        )
    def tick_elemento(self, ctx): ...
