from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Contenedor(Interaccion):
    """
    Metodo con el que un Elemento puede equiparse cosas que no son equipables (como el agua)

    Metodos abstractos:

    - anhadir(self, elemento: Elemento) -> bool

    - extraer(self, elemento: Elemento) -> Elemento

    - get_contenido(self) -> list[Elemento]
    """

    def __init__(self, capacidad: float, contenido: list[Elemento] = None,**kwargs):
        super().__init__(**kwargs)
        self.capacidad = capacidad
        self.contenido = contenido or []

    def esta_lleno(self) -> float:
        cantidad = 0.0
        for elemento in self.contenido:
            cantidad += elemento.volumen
        return cantidad

    @abstractmethod
    def anhadir(self, elemento: Elemento) -> bool: ...

    @abstractmethod
    def extraer(self, elemento: Elemento) -> Elemento: ...

    @abstractmethod
    def get_contenido(self) -> list[Elemento]: ...
