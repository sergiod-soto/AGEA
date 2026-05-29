from Core.Entities.Elementos.elemento import Elemento


class Elemento_Abstracto(Elemento):

    def __init__(self, tipo: type, **kwargs):
        super().__init__(
            tipo=tipo,
            capa=None,
            fuerza_sector_activo=False,
            fuerza_vecinos_activos=False,
            **kwargs
        )
