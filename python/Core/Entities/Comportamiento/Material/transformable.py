from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion
from Core.Entities.Elementos.elemento import Elemento


class Transformable(Material):
    """
    Elemento que, al darse una condicion, es cambiado por otro:

    Puede ser reversible, como agua -> hielo -> agua

    Parametros:

    - dict_transformable: dict[Condicion, Elemento]

    Metodos abstractos:

    - get_condiciones_transformable(self)
    """

    def __init__(self, dict_transformable: dict[Condicion, Elemento], **kwargs):
        super().__init__(**kwargs)
        self.dict_transformable = dict_transformable

    @abstractmethod
    def get_condiciones_transformable(self): ...
