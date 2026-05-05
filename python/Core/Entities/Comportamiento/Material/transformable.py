from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.elemento import Elemento


class Transformable(Material):
    """
    Elemento que, al darse una condicion, es cambiado por otro:

    Puede ser reversible, como agua -> hielo -> agua

    Parametros:

    - dict: dict[Condicion, Elemento]

    Metodos abstractos:

    - get_condiciones(self)
    """

    def __init__(self, dict: dict[Condicion, Elemento]):
        super().__init__()
        self.dict = dict

    @abstractmethod
    def get_condiciones(self): ...
