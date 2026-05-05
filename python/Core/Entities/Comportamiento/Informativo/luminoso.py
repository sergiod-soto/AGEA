from Core.Entities.Comportamiento.Informativo.informativo import Informativo


class Luminoso(Informativo):
    """
    Parametros:

    - distancia: float

    - area: int = 360
    """

    def __init__(self, distancia: float, area: int = 360):
        super().__init__()
        self.distancia = distancia
        if area < 0:
            self.area = 0
        else:
            self.area = area
