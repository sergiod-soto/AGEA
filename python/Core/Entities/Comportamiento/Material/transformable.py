from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.elemento import Elemento


class Transformable(Material):
    """
    Elemento que, al darse determinadas circunstancias, es cambiado por otro:
    madera (transformable) + calor -> ceniza.

    Puede ser reversible, como agua -> hielo -> agua
    """

    def __init__(self, dict: dict[Condicion, Elemento]):
        super().__init__()
        self.dict = dict
        
    def get_condiciones(self):
        pass
        
