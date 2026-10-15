# Core/Entities/Comportamiento/Interaccion/interactuable.py

from abc import abstractmethod
from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Interactuable(Interaccion):
    """
    Parametros:

    -

    Metodos abstractos:

    - interaccion(self, por:Elemento)
    """

    REQUIERE = {}
    ABSTRACTOS = {"def interaccion(self, por: Elemento)"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"interactuable": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"interactuable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @abstractmethod
    def interaccion(self, por: Elemento): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser interactuado (un botón, una palanca...).

Atributos:
\t-

Métodos:
\t@abstractmethod interaccion(self, por: Elemento)
\t--------------------------------------
\tInteractua.
        """
