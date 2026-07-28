from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Liquido(Material):
    """
    Parametros:

    -

    Metodos abstractos:

    -
    """

    def __init__(self, disuelto: list[Elemento] = None, **kwargs):
        super().__init__(**kwargs)
        self.disuelto = disuelto or []


    