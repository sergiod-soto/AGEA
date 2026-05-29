from Core.Entities.Elementos.elemento import Elemento


class Elemento_Compuesto(Elemento):

    def __init__(
        self,
        tipo: type,
        capa: int,
        fuerza_sector_activo: bool,
        fuerza_vecinos_activos: bool,
        **kwargs
    ):
        super().__init__(
            tipo=tipo,
            capa=capa,
            fuerza_sector_activo=fuerza_sector_activo,
            fuerza_vecinos_activos=fuerza_vecinos_activos,
            **kwargs
        )
