from elemento import Elemento


# la comida otorga energia. decae a lo largo del tiempo, otorgando cada
# vez menos energia. mas alla del minimo, reduce salud actual


class Comida(Elemento):

    def __init__(self):
        self.durabilidad = 100.0

    def energia(self):
        pass

