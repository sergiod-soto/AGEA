from Core.Entities.Comportamiento.Informativo.informativo import Informativo


class Luminoso(Informativo):
    """
    Parametros:

    - distancia: float

    - area: int = 360
    """

    def __init__(self, distancia_luz: float, area_luz: int = 360,**kwargs):
        super().__init__(**kwargs)
        self.distancia = distancia_luz
        if area_luz < 0:
            self.area = 0
        else:
            self.area = area_luz
