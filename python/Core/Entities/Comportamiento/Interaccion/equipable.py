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

    REQUIERE = {
        "provoca_equiparlo: dict[Elemento, Accion] = None",
        "equipado_por: Elemento = None",
    }
    ABSTRACTOS = {
        "def equipar(self, por: Elemento) -> bool",
        "def desequipar(self, por: Elemento) -> Elemento",
    }

    def __init__(self, provoca_equiparlo: dict[Elemento, Accion] = None, **kwargs):
        super().__init__(**kwargs)
        self.provoca_equiparlo = provoca_equiparlo
        self.equipado_por: Elemento = None

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"equipable": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"equipable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def _campos_internos(cls):
        return {"equipado_por"}

    @abstractmethod
    def equipar(self, por: Elemento) -> bool: ...

    @abstractmethod
    def desequipar(self, por: Elemento) -> Elemento: ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "provoca_equiparlo",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser incorporado por otro sin ser consumido.

Atributos:
\tprovoca_equiparlo: dict[Elemento, Accion] = None

Métodos:
\t@abstractmethod equipar(self, por: Elemento) -> bool
\t--------------------------------------
\tSe equipa.

\t@abstractmethod desequipar(self, por: Elemento) -> Elemento
\t--------------------------------------
\tSe desequipa.
            """
