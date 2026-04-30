from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple


# la comida otorga energia. decae a lo largo del tiempo, otorgando cada
# vez menos energia. mas alla del minimo, reduce salud actual


class Comida(Elemento_Simple):

    def __init__(self):
        self.durabilidad = 100.0

    def energia(self):
        pass
