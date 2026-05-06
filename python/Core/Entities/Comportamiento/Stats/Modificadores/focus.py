from Core.Entities.Comportamiento.Stats.Modificadores.modificador import Modificador


class Focus(Modificador):
    def __init__(self, valor: float = 0.0,**kwargs):
        super().__init__("focus", valor,**kwargs)
