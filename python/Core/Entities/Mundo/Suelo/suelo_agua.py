# Core/Entities/Mundo/Suelo/suelo_agua.py

from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Terreno.acuoso import Acuoso
from Core.Entities.Mundo.Suelo.suelo import Suelo
from Core.Entities.Comportamiento.comportamiento import Comportamiento



comportamientos = Comportamiento.declarar_comportamientos(
    Transformable,
)

class Suelo_Agua(Suelo, Acuoso, comportamientos):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Agua,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=92,
            inercia_termica=2.1e7,
            dict_transformable={},
        )
    def tick_elemento(self, ctx): ...
