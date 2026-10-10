# Core/Entities/Mundo/Suelo/suelo_hielo.py

from Core.Entities.Comportamiento.Terreno.helado import Helado
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Hielo(Suelo, Helado):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Hielo,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=35,
            inercia_termica=1.4e6,
        )
