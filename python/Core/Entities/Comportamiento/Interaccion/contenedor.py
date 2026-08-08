from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Contenedor(Interaccion):
    """
    Metodo con el que un Elemento puede equiparse cosas que no son equipables (como el agua)

    Parametros:

    - capacidad: float
    - contenido_contenedor: list[Elemento] = None

    Metodos abstractos:

    - anhadir(self, elemento: Elemento) -> bool
    - extraer(self, elemento: Elemento) -> Elemento
    - get_contenido(self) -> list[Elemento]
    """

    REQUIERE = {"capacidad_contenedor: float", ""}
    ABSTRACTOS = {
        "def anhadir(self, elemento: Elemento) -> bool",
        "def extraer(self, elemento: Elemento) -> Elemento",
        "def get_contenido(self) -> list[Elemento]",
    }

    def __init__(self, capacidad_contenedor: float, **kwargs):
        super().__init__(**kwargs)
        self.capacidad_contenedor = capacidad_contenedor
        self.contenido_contenedor = []

    @classmethod
    def _campos_internos(cls):
        return {"contenido_contenedor"}

    def esta_lleno(self) -> float:
        cantidad = 0.0
        for elemento in self.contenido_contenedor:
            cantidad += elemento.volumen
        return cantidad

    @abstractmethod
    def anhadir(self, elemento: Elemento) -> bool: ...

    @abstractmethod
    def extraer(self, elemento: Elemento) -> Elemento: ...

    @abstractmethod
    def get_contenido(self) -> list[Elemento]: ...
