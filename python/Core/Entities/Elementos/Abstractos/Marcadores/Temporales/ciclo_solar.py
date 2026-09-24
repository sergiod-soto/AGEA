# Core/Entities/Elementos/Abstractos/Marcadores/Temporales/ciclo_solar.py


from Config.parametros_simulacion import TICKS_POR_DIA
from Config.settings import ID_CICLO_SOLAR
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.Abstractos.Tiempo.reloj import Reloj


class Ciclo_Solar(Marcador_Temporal):
    def __init__(self, mundo, **kwargs):

        super().__init__(Ciclo_Solar, ID_CICLO_SOLAR, **kwargs)

        self.mundo = mundo
        self.ciclo: Reloj.Ciclo = self.mundo.reloj.agregar_ciclo(
            Ciclo_Solar, TICKS_POR_DIA * 1
        )

    # TODO: implementar. la hora depende de la estacion
    def get_hora_amanecer(self) -> int: ...
    def get_hora_anochecer(self) -> int: ...
    def get_hora_amanecer(self) -> int: ...
