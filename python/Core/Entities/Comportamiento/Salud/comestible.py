from abc import abstractmethod

from Core.Entities.Comportamiento.Stats.Simples.salud import Salud
from Core.Entities.Elementos.elemento import Elemento


class Comestible(Salud):
    """
    Se puede ingerir

    Parametros:

    -

    Metodos abstractos:

    - comer(self, por: Elemento)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def comer(self, por: Elemento): ...
