# Core/Mundo/mundo.py

from dataclasses import dataclass, field
from typing import Optional

from numpy import uint64

from Core.Entities.Mundo.Celda.celda_atmosfera import Celda_Atmosfera
from Core.Entities.Mundo.Celda.celda import Celda
from Core.Entities.Elementos.elemento import Elemento
from Infraestructura.Gestores.Mundo.Bus_Eventos.bus import BusEventos

"""
Este Mundo es El Mundo. 
Es el mapa que es dividido en chunks.
Gestiona como nodo central.

Es un elemento abstracto para tener comportamientos.

TODO: terminar. por ahora solo tiene el bus de eventos al que se suscriben ciertos Elementos
"""


class Mundo:
    """
    Orden actualizacion metereologia:
    - 1) radiacion
    - 2) temperatura
    - 3) presion
    - 4) viento
    - 5) humedad_absoluta
    - 6) nubes
    """

    def __init__(self):
        self.bus_eventos = BusEventos()

        # malla terreno
        self.ids = dict[
            uint64, tuple[int, int]
        ]  # id de las cosas que estan en la tierra. id -> posicion
        self.malla_terreno = dict[tuple[int, int], Celda]  # posicion -> Celda con cosas

        # malla atmosferica
        self.malla_atmosfera = dict[
            tuple[int, int], Celda_Atmosfera
        ]  # posicion -> Celda_Atmosfera con cosas de la atmosfera

    def eliminar_elemento(self, elemento: Elemento): ...  # TODO

    def agregar_elemento(self, elemento: Elemento):
        elemento.mundo = self
        # TODO: resto de agregar_elemento() en mundo.py

    def get_celda_atmosfera(self, posicion: tuple[int, int]): return self.malla_atmosfera
