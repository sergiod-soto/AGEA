# Core/Entities/Comportamiento/Temporal/regenerable.py

from abc import abstractmethod

from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Temporal.temporal import Temporal


class Regenerable(Temporal):
    """
    Indica que el Elemento tiene propiedades que regeneran con el tiempo

    Parametros:

    - tasas_regeneracion: list[tuple[Stat, float]]

    Metodos abstractos:

    - tick()
    """

    REQUIERE = {"tasas_regeneracion: list[tuple[Stat, float]]"}
    ABSTRACTOS = {"def tick_comportamiento(self):"}

    def __init__(self, tasas_regeneracion: list[tuple[Stat, float]], **kwargs):
        super().__init__(**kwargs)
        self.tasas_regeneracion = tasas_regeneracion

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"regenerable": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"regenerable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @abstractmethod
    def tick_comportamiento(self): ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Indica que el Elemento tiene propiedades que regeneran con el tiempo.

Parametros:
\ttasas_regeneracion: list[tuple[Stat, float]]

Métodos:
\t@abstractmethod tick()
\t--------------------------------------
\tComputa el siguiente tick.
        """
