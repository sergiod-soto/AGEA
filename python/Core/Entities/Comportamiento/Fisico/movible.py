from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Movible(Fisico):

    def __init__(self, gasto_energetico: float, movible: bool = True):
        super().__init__()
        self.gasto_energetico = gasto_energetico
        self.movible = movible
