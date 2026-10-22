# Core/Entities/Mundo/Suelo/suelo_arena.py

from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Terreno.arenoso import Arenoso
from Core.Entities.Mundo.Suelo.suelo import Suelo
from Core.Entities.Comportamiento.comportamiento import Comportamiento

comportamientos = Comportamiento.declarar_comportamientos(
    Transformable,
)

TASA_CONVERSION_ARENA = 65
INERCIA_TERMICA_ARENA = 3e5


class Suelo_Arena(Suelo, Arenoso, comportamientos):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Arena,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=TASA_CONVERSION_ARENA,
            inercia_termica=INERCIA_TERMICA_ARENA,
            dict_transformable={},
        )

    def tick_elemento(self, ctx): ...
