# Core/Entities/Mundo/Suelo/suelo_oceano.py

from Core.Entities.Comportamiento.Material.transformable import Transformable
from Core.Entities.Comportamiento.Terreno.oceanico import Oceanico
from Core.Entities.Mundo.Suelo.suelo import Suelo
from Core.Entities.Comportamiento.comportamiento import Comportamiento

comportamientos = Comportamiento.declarar_comportamientos(
    Transformable,
)

TASA_CONVERSION_OCEANO = 92
INERCIA_TERMICA_OCEANO = 2.1e7


class Suelo_Oceano(Suelo, Oceanico, comportamientos):
    """
    Suelo oceánico: tasa de conversión 92, inercia 2.1e7 J/(m²·K), solo la
    masa de agua; la capa de aire de la celda (C_AIRE) se cuenta aparte.
    """

    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Oceano,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=TASA_CONVERSION_OCEANO,
            inercia_termica=INERCIA_TERMICA_OCEANO,
            dict_transformable={},
        )

    def tick_elemento(self, ctx): ...
