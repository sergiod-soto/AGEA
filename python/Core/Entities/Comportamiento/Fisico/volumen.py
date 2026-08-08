from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Volumen(Fisico):
    """
    (cm3)

    Parametros:

    - volumen: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"volumen: float"}
    ABSTRACTOS = {}

    def __init__(self, volumen: float, **kwargs):
        super().__init__(**kwargs)
        self.volumen = volumen
