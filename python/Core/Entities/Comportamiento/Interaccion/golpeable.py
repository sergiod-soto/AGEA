from abc import abstractmethod

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Golpeable(Material):
    """
    Parametros:

    -

    Metodos abstractos:

    - golpear(self, por: Elemento)
    """

    REQUIERE = {}
    ABSTRACTOS = {"def golpear(self, por: Elemento)"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.golpeable = True

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"golpeable": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"golpeable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def _campos_internos(cls):
        return {"golpeable"}

    @abstractmethod
    def golpear(self, por: Elemento): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser interactuado con "golpear".

Atributos:
\t-

Métodos:
\t@abstractmethod golpear(self, por: Elemento)
\t--------------------------------------
\tSe golpea al Elemento por el Elemento "por"
        """
