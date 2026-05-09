from abc import abstractmethod
from typing import Callable

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Transformable(Material):
    """
    Elemento que, al darse una condicion, es cambiado por otro:

    Puede ser reversible, como agua -> hielo -> agua

    El Callable es la funcion que transforma al Elemento

    Parametros:

    - dict_transformable: dict[Condicion, Callable]

    Metodos abstractos:

    -
    """

    def __init__(self, dict_transformable: dict[Condicion, Callable], **kwargs):
        super().__init__(**kwargs)
        self.dict_transformable = dict_transformable

    def get_condiciones(self) -> list[Condicion]:
        return list(self.dict_transformable.keys())
