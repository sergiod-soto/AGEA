from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.elemento import Elemento


class Equipable(Interaccion):
    """
    Elemento que puede ser equipado por un elemento que no necesariamente tiene por que ser contenedor
    
    Parametros:
    
    - provoca_equiparlo: dict[Elemento, Accion] = None
    - equipado_por: Elemento = None

    Metodos abstractos:

    - equipar(self, por: Elemento) -> bool
    - desequipar(self, por: Elemento) -> Elemento
    """

    def __init__(
        self,
        provoca_equiparlo: dict[Elemento, Accion] = None,
        equipado_por: Elemento = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.provoca_equiparlo = provoca_equiparlo
        self.equipado_por = equipado_por

    
    @abstractmethod
    def equipar(self, por: Elemento) -> bool: ...

    @abstractmethod
    def desequipar(self, por: Elemento) -> Elemento: ...
