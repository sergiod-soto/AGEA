# Core/Mundo/mundo.py
from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Entities.Elementos.Abstractos.Informacion.luz_ambiental import Luz_Ambiental
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.ciclo_lunar import (
    Ciclo_Lunar,
)
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.clima import Clima
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.estacion import Estacion
from Core.Entities.Elementos.elemento import Elemento
from Infraestructura.Gestores.Mundo.Bus_Eventos.bus import BusEventos

"""
Este Mundo es El Mundo. 
Es el mapa que es dividido en chunks.
Gestiona como nodo central.

Es un elemento abstracto para tener comportamientos.

TODO: terminar. por ahora solo tiene el bus de eventos al que se suscriben ciertos Elementos
"""

informacion_abstracta = Comportamiento.declarar_comportamientos(
    Luz_Ambiental,
)

marcadores = Comportamiento.declarar_comportamientos(
    Ciclo_Lunar,
    Clima,
    Estacion,
)


class Mundo(informacion_abstracta, marcadores):

    def __init__(self, tipo, **kwargs):
        super().__init__(tipo, **kwargs)
        self.bus = BusEventos()
        Elemento.mundo = self
