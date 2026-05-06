from Core.Entities.Comportamiento.Stats.stat import Stat


class Informacion(Stat):
    def __init__(self, nombre, valor,**kwargs):
        super().__init__(nombre, valor,**kwargs)
