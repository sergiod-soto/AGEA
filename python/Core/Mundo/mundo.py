from Core.Mundo.Bus_Eventos.bus import BusEventos


class Mundo:
    def __init__(self): 
        self.bus = BusEventos()
