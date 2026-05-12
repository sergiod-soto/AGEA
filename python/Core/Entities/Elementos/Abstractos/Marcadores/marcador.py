from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Marcador(Elemento_Abstracto):
    def __init__(self, **kwargs):
        super().__init__(Marcador, **kwargs)
