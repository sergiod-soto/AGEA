from Core.Entities.Comportamiento.Stats.Modificadores.modificador import Modificador


class Herida(Modificador):
    def __init__(self, valor: float = 0.0,**kwargs):
        super().__init__("heridas", valor,**kwargs)
