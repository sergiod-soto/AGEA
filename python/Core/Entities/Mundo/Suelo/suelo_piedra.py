# Core/Entities/Mundo/Suelo/suelo_piedra.py

from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Terreno.rocoso import Rocoso
from Core.Entities.Mundo.Suelo.suelo import Suelo
from Core.Entities.Comportamiento.comportamiento import Comportamiento

comportamientos = Comportamiento.declarar_comportamientos(
    Transformable,
)

TASA_CONVERSION_PIEDRA = 75
INERCIA_TERMICA_PIEDRA = 4e5


class Suelo_Piedra(Suelo, Rocoso, comportamientos):
    """
    Suelo de piedra: tasa de conversión 75, inercia 4e5 J/(m²·K).
    La inercia es solo la masa del suelo que responde al ciclo diario: la
    capa de aire de la celda (C_AIRE) se cuenta aparte en la temperatura.
    """

    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Piedra,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=TASA_CONVERSION_PIEDRA,
            inercia_termica=INERCIA_TERMICA_PIEDRA,
            dict_transformable={},
        )

    def tick_elemento(self, ctx): ...
