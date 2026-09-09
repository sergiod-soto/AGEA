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
    ABSTRACTOS = {"def tick(self):"}

    def __init__(self, tasas_regeneracion: list[tuple[Stat, float]], **kwargs):
        super().__init__(**kwargs)
        self.tasas_regeneracion = tasas_regeneracion

    @abstractmethod
    def tick(self): ...

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
