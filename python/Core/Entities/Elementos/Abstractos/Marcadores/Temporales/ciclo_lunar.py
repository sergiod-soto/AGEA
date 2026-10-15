# Core/Entities/Elementos/Abstractos/Marcadores/Temporales/ciclo_lunar.py

import math

from Config.settings import ID_CICLO_LUNAR
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.Abstractos.Tiempo.reloj import Reloj


class Ciclo_Lunar(Marcador_Temporal):
    """
    Dueña del Reloj.Ciclo lunar. `frecuencia_lunar` es la duración del ciclo
    en DÍAS simulados (la conversión a ticks la hace el Reloj, así que no
    depende de cuántos segundos simule cada tick).
    """

    def __init__(self, mundo, frecuencia_lunar: int = 30, **kwargs):
        super().__init__(Ciclo_Lunar, ID_CICLO_LUNAR, **kwargs)
        self.mundo = mundo
        self._frecuencia_lunar = frecuencia_lunar
        self.ciclo: Reloj.Ciclo = self.mundo.reloj.agregar_ciclo(
            self, self.mundo.reloj.Dia(frecuencia_lunar)
        )

    @staticmethod
    def intensidad_para_progreso(progreso: float) -> float:
        """[0, 1]: 0 en luna nueva (progreso 0), 1 en llena (0.5)."""
        return 0.5 * (1 - math.cos(2 * math.pi * progreso))

    def get_intensidad_luna(self) -> float:
        return self.intensidad_para_progreso(self.ciclo.progreso)
