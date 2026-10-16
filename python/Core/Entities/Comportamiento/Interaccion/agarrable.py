# Core/Entities/Comportamiento/Interaccion/agarrable.py

from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Agarrable(Interaccion):
    """
    Forma en la que un Elemento puede ser desplazado por otro de forma directa, sin "empujar"

    Parametros:

    - agarrado_por: int = None   (id_elemento de quien lo agarra, None si nadie)

    Se usa el ID y no el objeto: en un Sector no hay Mundo para resolver ids a
    objetos, así que el atributo es un entero en TODOS los procesos.

    Metodos abstractos:

    - agarrar(self, por: int)
    - soltar(self, por: int)
    """

    REQUIERE = {
        "agarrado_por: int = None",
    }

    ABSTRACTOS = {
        "def agarrar(self, por: int)",
        "def soltar(self, por: int)",
    }

    def __init__(self, agarrado_por: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self.agarrado_por = agarrado_por

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "agarrado_por": self.agarrado_por,
        }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.agarrado_por = data["comportamientos"][__class__.__name__]["agarrado_por"]

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"agarrable": {}}
        return datos

    @abstractmethod
    def agarrar(self, por: int):
        """Accion pasiva. `por` es el id_elemento de quien tiene intencion de agarrar este elemento."""
        ...

    @abstractmethod
    def soltar(self, por: int):
        """Accion pasiva. `por` es el id_elemento de quien tiene intencion de soltar este elemento."""
        ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "agarrado_por",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser agarrado por otro Elemento.

Atributos:
\tagarrado_por: Elemento = None

Métodos:
\t@abstractmethod agarrar(self, por: Elemento)
\t--------------------------------------
\tSe intenta agarrar.

\t@abstractmethod soltar(self, por: Elemento)
\t--------------------------------------
\tSe intenta soltar
        """
