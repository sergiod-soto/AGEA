from Gestores.Mundo.Bus_Eventos.bus import BusEventos

"""
Este Mundo es El Mundo. 
Es el mapa que es dividido en chunks.
Gestiona como nodo central.

_________________________________________________
implementacion de logs de los hypervisores:

from core.log_server import LogServer

log_server = LogServer(host="[::]:50060", log_dir="logs/")
log_server.start()   # configura logs/mundo.log y arranca el servidor
"""


class Mundo:
    def __init__(self):
        self.bus = BusEventos()
