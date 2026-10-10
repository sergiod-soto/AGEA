from Core.Entities.Elementos.Abstractos.Marcadores.marcador import Marcador


class Marcador_Temporal(Marcador):
    """ """

    def __init__(self, tipo: type, id_elemento: int, **kwargs):
        super().__init__(tipo, id_elemento, **kwargs)
