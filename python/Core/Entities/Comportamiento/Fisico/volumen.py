from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Volumen(Fisico):

    def __init__(self, volumen: float):
        super().__init__()
        self.volumen = volumen
