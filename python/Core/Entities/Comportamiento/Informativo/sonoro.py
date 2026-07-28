from Core.Entities.Comportamiento.Informativo.informativo import Informativo
from Core.Entities.Elementos.Abstractos.Informacion.sonido import Sonido


class Sonoro(Informativo):
    """
    Parametros:

    - sonidos: dict[str, list[Sonido]]

    Metodos abstractos:

    -
    """

    def __init__(self, sonidos: dict[str, list[Sonido]], **kwargs):
        super().__init__(**kwargs)
        self.sonidos = sonidos

