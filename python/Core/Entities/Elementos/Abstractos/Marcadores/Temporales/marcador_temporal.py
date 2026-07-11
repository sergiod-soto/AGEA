from Core.Entities.Elementos.Abstractos.Marcadores.marcador import Marcador


class Marcador_Temporal(Marcador):
    """ """

    def __init__(self, tipo: type, **kwargs):
        super().__init__(tipo, **kwargs)
