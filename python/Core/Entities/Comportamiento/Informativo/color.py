from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Color(Comportamiento):
    """
    Color del Elemento en RGB

    Parametros:

    -  rgb: tuple[int, int, int]
    """

    def __init__(self, rgb: tuple[int, int, int],**kwargs):
        super().__init__(**kwargs)
        self.rgb = rgb
