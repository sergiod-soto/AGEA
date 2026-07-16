from Core.Entities.Elementos.elemento import Elemento


class Elemento_Simple(Elemento):
    """
    - tipo,
    - tamanho: int,
    - casilla: tuple[int, int],
    - capa: int,
    - rotacion: float = 0,
    - fuerza_sector_activo: bool = False,
    - fuerza_vecinos_activos: bool = False,
    """

    def __init__(
        self,
        tipo,
        id,
        tamanho: int,
        casilla: tuple[int, int],
        capa: int,
        rotacion: float = 0,
        fuerza_sector_activo: bool = False,
        fuerza_vecinos_activos: bool = False,
        **kwargs,
    ):
        super().__init__(
            tipo=tipo,
            capa=capa,
            id=id,
            fuerza_sector_activo=fuerza_sector_activo,
            fuerza_vecinos_activos=fuerza_vecinos_activos,
            **kwargs,
        )
        self.tamanho = tamanho
        self.casilla = casilla
        self.rotacion = rotacion

    def serialize_tamanho(self):
        return self.tamanho

    def serialize_capa(self):
        return self.capa

    def serialize_casilla(self):
        return str({"x": self.casilla[0], "y": self.casilla[1]})

    def serialize_rotacion(self):
        return self.rotacion % 360
