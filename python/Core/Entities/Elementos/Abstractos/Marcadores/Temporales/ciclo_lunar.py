# Core/Entities/Elementos/Abstractos/Marcadores/Temporales/ciclo_lunar.py


import math

from Config.parametros_simulacion import TICKS_POR_DIA
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.Abstractos.Tiempo.reloj import Reloj


class Ciclo_Lunar(Marcador_Temporal):

    def __init__(self, frecuencia_lunar=30, **kwargs):
        super().__init__(Ciclo_Lunar, **kwargs)
        self._frecuencia_lunar = frecuencia_lunar
        self.ciclo: Reloj.Ciclo = self.mundo.agregar_ciclo(
            Ciclo_Lunar, TICKS_POR_DIA * 30
        )

    def get_intensidad_luna(self) -> int:
        progreso = self.ciclo.tick_actual / self._frecuencia_lunar
        return 10 * (1 - math.cos(2 * math.pi * progreso))
