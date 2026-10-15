# Core/Entities/Elementos/Abstractos/Marcadores/Temporales/ciclo_anual.py

from Config.settings import ID_CICLO_ANUAL
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)
from Core.Entities.Elementos.Abstractos.Tiempo.reloj import Reloj


class Ciclo_Anual(Marcador_Temporal):
    """
    Dueño del Reloj.Ciclo de un año simulado. Es CONTINUO (paso=1): su
    .progreso alimenta la declinación solar de la atmósfera. No sabe nada de
    estaciones (de eso se ocupa Estaciones).
    """

    def __init__(self, mundo, **kwargs):
        super().__init__(Ciclo_Anual, ID_CICLO_ANUAL, **kwargs)
        self.mundo = mundo
        self.ciclo: Reloj.Ciclo = self.mundo.reloj.agregar_ciclo(
            self, self.mundo.reloj.Anho(1)
        )
