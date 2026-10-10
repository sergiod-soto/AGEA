from abc import abstractmethod

from Core.Entities.Comportamiento.Temporal.temporal import Temporal
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Perecedero(Temporal):
    """
    Durabilidad decae con el tiempo a un ritmo diferente segun condiciones.

    Parametros:

    - tiempo_maximo_perecedero: float
    - condiciones_perecedero: list[tuple[list[Condicion], float]]
    - tiempo_actual_perecedero: float = None

    Metodos abstractos:

    - tick() -> None
    - desaparecer() -> None
    """

    REQUIERE = {
        "tiempo_maximo_perecedero: float",
        "condiciones_perecedero: list[tuple[list[Condicion], float]]",
        "tiempo_actual_perecedero: float = None",
    }
    ABSTRACTOS = {
        "def tick(self) -> None",
        "def desaparecer(self) -> None",
    }

    def __init__(
        self,
        tiempo_maximo_perecedero: float,
        condiciones_perecedero: list[tuple[list[Condicion], float]],
        tiempo_actual_perecedero: float = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.tiempo_maximo_perecedero = tiempo_maximo_perecedero
        self.tiempo_actual_perecedero = (
            tiempo_actual_perecedero or tiempo_maximo_perecedero
        )
        self.condiciones_perecedero = condiciones_perecedero

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"perecedero": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"perecedero": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @abstractmethod
    def tick(self) -> None: ...

    @abstractmethod
    def desaparecer(self) -> None: ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento se degrada hasta desaparecer con el tiempo.

Atributos:
\ttiempo_maximo_perecedero: float
\tcondiciones_perecedero: list[tuple[list[Condicion], float]]
\ttiempo_actual_perecedero: float = None

Métodos:
\t@abstractmethod tick(self) -> None
\t--------------------------------------
\tComputa el siguiente tick.

\t@abstractmethod desaparecer(self) -> None
\t--------------------------------------
\tEl Elemento se ha degradado al máximo.
        """
