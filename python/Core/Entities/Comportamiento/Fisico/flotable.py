from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Flotable(Fisico):
    def __init__(self, flotable: bool = True):
        super().__init__()
        self.flotable = flotable
