from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Empujable(Fisico):

    def __init__(self, gasto_energetico: float, empujable: bool = True):
        super().__init__()
        self.gasto_energetico = gasto_energetico    #   cuanta energia drena moverlo 1 ud.
        self.empujable = empujable