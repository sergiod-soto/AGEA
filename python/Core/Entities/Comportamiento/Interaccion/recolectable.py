# Core/Entities/Comportamiento/Interaccion/recolectable.py

from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Recolectable(Interaccion):
    """
    Indica si puede ser recolectardo para obtener Elemento(s)

    Parametros:

    - contenido_recolectable: dict[str, tuple[Elemento, float]] = None

    Metodos abstractos:

    - recolectar(self, por: Elemento)
    """

    REQUIERE = {"contenido_recolectable: dict[str, tuple[Elemento, float]] = None"}
    ABSTRACTOS = {"def recolectar(self, por: Elemento)"}

    def __init__(
        self, contenido_recolectable: dict[str, tuple[Elemento, float]] = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.contenido_recolectable = contenido_recolectable or {}

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"recolectable": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"recolectable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @abstractmethod
    def recolectar(self, por: Elemento): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser recolectado para la generacion de otro Elemento.

Atributos:
\tcontenido_recolectable: dict[str, tuple[Elemento, float]] = None

Métodos:
\t@abstractmethod recolectar(self, por: Elemento)
\t--------------------------------------
\tProvoca la generacion del recurso, si posible.
        """
