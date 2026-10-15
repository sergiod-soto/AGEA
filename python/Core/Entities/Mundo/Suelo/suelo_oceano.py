# Core/Entities/Mundo/Suelo/suelo_oceano.py

from Core.Entities.Comportamiento.Terreno.oceanico import Oceanico
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Oceano(Suelo, Oceanico):
    """
    Suelo oceánico: tasa de conversión 92, inercia 2.2e7 J/(m²·K).
    La inercia INCLUYE ~1e6 J/(m²·K) de la capa de aire de la celda (la
    temperatura es única por celda); el resto es la masa de agua.
    """

    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Oceano,
            casilla=casilla,
            id_elemento=id_elemento,
            tasa_conversion_radiacion_calor=92,
            inercia_termica=2.2e7,
        )
