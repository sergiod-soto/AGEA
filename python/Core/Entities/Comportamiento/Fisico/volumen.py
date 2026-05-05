from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Volumen(Fisico):
    """
    Parametros:

    - volumen: float
    """

    def __init__(self, volumen: float):
        super().__init__()
        self.volumen = volumen
