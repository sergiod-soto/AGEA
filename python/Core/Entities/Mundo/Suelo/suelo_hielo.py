# Core/Entities/Mundo/Suelo/suelo_hielo.py

from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Terreno.helado import Helado
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Mundo.Suelo.suelo import Suelo

comportamientos = Comportamiento.declarar_comportamientos(
    Transformable,
)

TASA_CONVERSION_HIELO = 35
INERCIA_TERMICA_HIELO = 4e5


class Suelo_Hielo(Suelo, Helado, comportamientos):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Hielo,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=TASA_CONVERSION_HIELO,
            inercia_termica=INERCIA_TERMICA_HIELO,
            dict_transformable={},
        )

    def tick_elemento(self, ctx): ...
