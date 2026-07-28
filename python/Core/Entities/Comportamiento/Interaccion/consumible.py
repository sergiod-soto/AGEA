from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Consumible(Interaccion):
    """
    Todo lo que puede ser consumido por otro Elemento.
    
    NO ES SER COMIDO/BEBIDO, ESO ES COMESTIBLE, esto es,
    por ejemplo, madera en una hoguera, la tiza al escribir, etc

    Parametros:

    -

    Metodos abstractos:

    - consumir(self, por: Elemento)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def consumir(self, por: Elemento): ...

    