# Core/Entities/Mundo/Suelo/suelo_cesped.py

from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Terreno.herboso import Herboso
from Core.Entities.Mundo.Suelo.suelo import Suelo
from Core.Entities.Comportamiento.comportamiento import Comportamiento



comportamientos = Comportamiento.declarar_comportamientos(
    Transformable,
)

class Suelo_Cesped(Suelo, Herboso, comportamientos):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Cesped,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=75,
            inercia_termica=3e5,
            dict_transformable={},
        )
    def tick_elemento(self, ctx): ...