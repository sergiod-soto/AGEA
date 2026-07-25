from Config.parametros_simulacion import TICKS_POR_DIA
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.Abstractos.Tiempo.reloj import Reloj


class Ciclo_Solar(Marcador_Temporal):
    def __init__(self, **kwargs):
        super().__init__(Ciclo_Solar, **kwargs)
        self.ciclo: Reloj.Ciclo = self.mundo.agregar_ciclo(
            Ciclo_Solar, TICKS_POR_DIA * 1
        )

    def get_hora_amanecer(self) -> int: ...
    def get_hora_anochecer(self) -> int: ...
    def get_hora_amanecer(self) -> int: ...
