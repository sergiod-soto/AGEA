from Core.Entities.Elementos.Abstractos.Bioma.bioma import Bioma


class Sub_Bioma(Bioma):

    def __init__(self, tipo, **kwargs):
        super().__init__(tipo, **kwargs)
