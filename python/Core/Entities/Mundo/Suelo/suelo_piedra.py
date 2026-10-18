# Core/Entities/Mundo/Suelo/suelo_piedra.py

from Core.Entities.Comportamiento.Terreno.rocoso import Rocoso
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Piedra(Suelo, Rocoso):
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
            tasa_conversion_radiacion_calor=75,
            inercia_termica=4e5,
        )

    def representar(self, incluir: list[str] | None = None) -> dict:
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["elemento"][
                "tasa_conversion_radiacion_calor"
            ] = self.tasa_conversion_radiacion_calor
            datos["elemento"]["inercia_termica"] = self.inercia_termica
        return datos

    def tick_elemento(self, ctx): ...
