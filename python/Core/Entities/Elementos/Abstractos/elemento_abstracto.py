# Core/Entities/Elementos/Abstractos/elemento_abstracto.py


from numpy import uint64

from Core.Entities.Elementos.elemento import Elemento


class Elemento_Abstracto(Elemento):

    def __init__(self, tipo: type, id_elemento: uint64, **kwargs):
        super().__init__(
            tipo=tipo,
            id_elemento=id_elemento,
            capa=0,
            **kwargs,
        )
