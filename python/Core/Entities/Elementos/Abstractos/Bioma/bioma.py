from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Bioma(Elemento_Abstracto):

    def __init__(self, tipo, **kwargs):
        super().__init__(tipo, **kwargs)
