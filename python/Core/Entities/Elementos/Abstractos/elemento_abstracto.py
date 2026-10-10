# Core/Entities/Elementos/Abstractos/elemento_abstracto.py


from Core.Entities.Elementos.elemento import Elemento


class Elemento_Abstracto(Elemento):

    def __init__(self, tipo: type, id_elemento: int, **kwargs):
        super().__init__(
            tipo=tipo,
            id_elemento=id_elemento,
            capa=0,
            **kwargs,
        )
