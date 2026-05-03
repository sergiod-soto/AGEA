from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.elemento import Elemento


class Equipable(Interaccion):
    def __init__(
        self,
        provoca_equiparlo: dict[Elemento, Accion] = None,
        equipado_por: Elemento = None,
    ):
        super().__init__()
        self.provoca_equiparlo = provoca_equiparlo
        self.equipado_por = equipado_por

    @abstractmethod
    def equipar(self, por: Elemento): ...

    @abstractmethod
    def desequipar(self, por: Elemento): ...
