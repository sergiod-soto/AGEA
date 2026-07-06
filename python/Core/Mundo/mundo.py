# Core/Mundo/mundo.py
from Infraestructura.Gestores.Mundo.Bus_Eventos.bus import BusEventos

"""
Este Mundo es El Mundo. 
Es el mapa que es dividido en chunks.
Gestiona como nodo central.

TODO: terminar. por ahora solo tiene el bus de eventos al que se suscriben ciertos Elementos
"""


class Mundo:
    def __init__(self):
        self.bus = BusEventos()
