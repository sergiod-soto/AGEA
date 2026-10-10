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

    REQUIERE = {}
    ABSTRACTOS = {"def consumir(self, por: Elemento)"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"consumible": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"consumible": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @abstractmethod
    def consumir(self, por: Elemento): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser destruido por otro para obtener efectos.

Atributos:
\t-

Métodos:
\t@abstractmethod consumir(self, por: Elemento)
\t--------------------------------------
\tSe consume.
        """
