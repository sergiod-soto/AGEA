from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple


class Etereo(Elemento_Simple):
    def __init__(
        self,
        tipo,
        tamanho,
        casilla,
        capa,
        rotacion=0,
        fuerza_sector_activo=False,
        fuerza_vecinos_activos=False,
        **kwargs
    ):
        super().__init__(
            tipo,
            tamanho,
            casilla,
            capa,
            rotacion,
            fuerza_sector_activo,
            fuerza_vecinos_activos,
            **kwargs
        )
