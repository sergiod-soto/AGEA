from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Enterrable(Fisico):

    def __init__(self, enterrable: bool = True):
        super().__init__()
        self.enterrable = enterrable
