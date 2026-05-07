from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Color(Comportamiento):
    """
    Color del Elemento en RGB

    Parametros:

    -  rgb_color: tuple[int, int, int]
    
    Metodos abstractos:
    
    -
    """

    def __init__(self, rgb_color: tuple[int, int, int],**kwargs):
        super().__init__(**kwargs)
        self.rgb = rgb_color
