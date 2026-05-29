from Core.Entities.Comportamiento.Fisico.fisico import Fisico
from Exceptions.Bot.comportamientos_exceptions import Peso_Zero


class Peso(Fisico):
    """
    (g)

    NO indica que algo pese mucho, si no que tiene masa

    Parametros:

    - peso: float

    Metodos abstractos:

    -
    """

    def __init__(self, peso: float, **kwargs):
        super().__init__(**kwargs)
        self.peso = peso
