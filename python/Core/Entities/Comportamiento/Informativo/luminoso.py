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
        self, distancia_luz: float, area_luz: float = 360, direccion_luz: float = 0, **kwargs
    ):
        super().__init__(**kwargs)
        self.distancia_luz = distancia_luz
        if area_luz < 0:
            self.area_luz = 0
            self.direccion_luz = 0
        else:
            self.area_luz = area_luz
            self.direccion_luz = direccion_luz


