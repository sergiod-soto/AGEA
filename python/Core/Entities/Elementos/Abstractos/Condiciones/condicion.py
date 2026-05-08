from abc import abstractmethod

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto
from Core.Entities.Comportamiento.comportamiento import Comportamiento as C
from Core.Entities.Elementos.elemento import Elemento

comportamientos = C.declarar_comportamientos()


class Condicion(Elemento_Abstracto):

    def __init__(self):
        super().__init__(Condicion)
        self.activa: bool = False

        """Cada subclase se suscribe a los eventos relevantes en __init__"""
        pass

    def _activar(self) -> None:
        self.activa = True
        Elemento.mundo.bus.emitir(f"condicion_activa_{id(self)}")

    def _desactivar(self) -> None:
        self.activa = False
        Elemento.mundo.bus.emitir(f"condicion_inactiva_{id(self)}")

    @abstractmethod
    def evaluar(self, contexto: dict) -> bool: ...
