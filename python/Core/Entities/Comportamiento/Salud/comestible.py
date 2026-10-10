from abc import abstractmethod

from Core.Entities.Comportamiento.Salud.salud import Salud
from Core.Entities.Elementos.elemento import Elemento


class Comestible(Salud):
    """
    Se puede ingerir

    Parametros:

    -

    Metodos abstractos:

    - comer(self, por: Elemento)
    """

    REQUIERE = {}
    ABSTRACTOS = {"def comer(self, por: Elemento)"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"comestible": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"comestible": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @abstractmethod
    def comer(self, por: Elemento): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "peso",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Puede ser asimilado (comido).

Atributos:
\t-

Métodos:
\t@abstractmethod comer(self, por: Elemento)
\t--------------------------------------
\tEl efecto que produce al Elemento ser asimilado.
        """
