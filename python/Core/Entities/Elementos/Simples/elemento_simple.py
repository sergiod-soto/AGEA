# Core/Entities/Elementos/Simples/elemento_simple.py

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
        id_elemento,
        tamanho: int,
        casilla: tuple[int, int],
        capa: int,
        rotacion: float = 0,
        **kwargs,
    ):
        super().__init__(
            tipo=tipo,
            capa=capa,
            id_elemento=id_elemento,
            **kwargs,
        )
        self.tamanho = tamanho
        self.casilla = casilla
        self.rotacion = rotacion

    def serialize_casilla(self):
        return {"x": self.casilla[0], "y": self.casilla[1]}

    def deserialize_casilla(self, value):
        self.casilla = (value["x"], value["y"])

    # 'rotacion' se normaliza a [0, 360) al serializar.
    def serialize_rotacion(self):
        return self.rotacion % 360
