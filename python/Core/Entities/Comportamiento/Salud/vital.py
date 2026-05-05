from Core.Entities.Comportamiento.Salud.salud import Salud
from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Vital(Salud):
    """
    Indica que el elemento tiene un contador de salud

    Parametros:

    - salud_maxima: int

    - salud_actual: int = None
    """

    def __init__(self, salud_maxima: int, salud_actual: int = None):
        super().__init__()
        self.salud_maxima = salud_maxima
        self.salud_actual = salud_actual or salud_maxima
