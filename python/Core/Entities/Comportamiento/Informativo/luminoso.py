from Core.Entities.Comportamiento.Informativo.informativo import Informativo


class Luminoso(Informativo):
    """
    Parametros:

    - distancia: float
    - area: float = 360
    - direccion: float = 0

    Metodos abstractos:

    -
    """

    def __init__(
        self, distancia_luz: float, area_luz: float = 360, direccion: float = 0, **kwargs
    ):
        super().__init__(**kwargs)
        self.distancia = distancia_luz
        if area_luz < 0:
            self.area = 0
            self.direccion = 0
        else:
            self.area = area_luz
            self.direccion = direccion
