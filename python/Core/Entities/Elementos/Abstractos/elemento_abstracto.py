# Core/Entities/Elementos/Abstractos/elemento_abstracto.py


from Core.Entities.Elementos.elemento import Elemento


class Elemento_Abstracto(Elemento):

    def __init__(self, tipo: type, **kwargs):
        super().__init__(
            tipo=tipo,
            capa=0,
            fuerza_sector_activo=False,
            fuerza_vecinos_activos=False,
            **kwargs
        )
