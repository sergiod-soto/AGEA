from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Flotable(Fisico):
    def __init__(self):
        super().__init__()
        self.flotable = True
