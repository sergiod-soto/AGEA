from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Sistema_Atmosferico(Elemento_Abstracto):
    """ """

    def __init__(self, tipo: type, id_elemento, **kwargs):
        super().__init__(tipo, id_elemento, **kwargs)
