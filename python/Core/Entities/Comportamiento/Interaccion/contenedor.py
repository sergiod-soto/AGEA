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

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"contenedor": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"contenedor": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def _campos_internos(cls):
        return {"contenido_contenedor"}

    def get_espacio_usado(self) -> float:
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

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "capacidad_contenedor",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede almacenar otros Elementos.

Atributos:
\tcapacidad_contenedor: float

Métodos:
\tget_espacio_usado(self) -> float
\t--------------------------------------
\tRetorna cuanto espaci se encuentra actualmente ocupado.

\t@abstractmethod anhadir(self, elemento: Elemento) -> bool
\t--------------------------------------
\tGuarda un Elemento.

\t@abstractmethod get_contenido(self) -> list[Elemento]
\t--------------------------------------
\tRetorna una lista con su contenido actual.
        """
