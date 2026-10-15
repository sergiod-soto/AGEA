# Core/Entities/Elementos/Abstractos/Marcadores/Temporales/ciclo_solar.py

from Config.settings import ID_CICLO_SOLAR
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.Abstractos.Tiempo.reloj import Reloj


class Ciclo_Solar(Marcador_Temporal):
    """Dueña del Reloj.Ciclo de un día simulado."""

    def __init__(self, mundo, **kwargs):
        super().__init__(Ciclo_Solar, ID_CICLO_SOLAR, **kwargs)
        self.mundo = mundo
        self.ciclo: Reloj.Ciclo = self.mundo.reloj.agregar_ciclo(
            self, self.mundo.reloj.Dia(1)
        )

    # TODO: implementar. La hora depende de la estación.
    def get_hora_amanecer(self) -> int: ...
    def get_hora_anochecer(self) -> int: ...