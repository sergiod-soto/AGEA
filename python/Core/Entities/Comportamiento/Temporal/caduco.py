# Core/Entities/Comportamiento/Temporal/caduco.py

from abc import abstractmethod

from Core.Entities.Comportamiento.Temporal.temporal import Temporal


class Caduco(Temporal):
    """
    Durabilidad decae con el tiempo

    Parametros:

    - duracion_max_caduco: int
    - duracion_restante_caduco: int = None

    Metodos abstractos:

    - tick() -> None
    - desaparecer() -> None
    """

    REQUIERE = {"duracion_max_caduco: int", ""}
    ABSTRACTOS = {"def tick_comportamiento(self) -> None", "def desaparecer(self) -> None"}

    def __init__(
        self, duracion_max_caduco: int, duracion_restante_caduco: int = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.duracion_max_caduco = duracion_max_caduco
        self.duracion_restante_caduco = duracion_restante_caduco or duracion_max_caduco

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"caduco": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"caduco": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @abstractmethod
    def tick_comportamiento(self) -> None: ...

    @abstractmethod
    def desaparecer(self) -> None: ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return ["duracion_max_caduco", "duracion_restante_caduco"]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento tiene una durabilidad que se reduce con el tiempo.

Atributos:
\tduracion_max_caduco: int,
\tduracion_restante_caduco: int = None,

Métodos:
\t@abstractmethod tick(self) -> None
\t--------------------------------------
\tComputa el siguiente tick.

\t@abstractmethod desaparecer(self) -> None
\t--------------------------------------
\tEl Elemento ha caducado.
        """
