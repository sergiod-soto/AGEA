from Core.Entities.Elementos.Abstractos.Bioma.bioma import Bioma


class Bioma_Principal(Bioma):

    def __init__(self, tipo, **kwargs):
        super().__init__(tipo, **kwargs)
