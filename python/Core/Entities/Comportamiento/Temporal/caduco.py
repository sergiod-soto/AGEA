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
    ABSTRACTOS = {"def tick(self) -> None", "def desaparecer(self) -> None"}

    def __init__(
        self, duracion_max_caduco: int, duracion_restante_caduco: int = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.duracion_max_caduco = duracion_max_caduco
        self.duracion_restante_caduco = duracion_restante_caduco or duracion_max_caduco

    @abstractmethod
    def tick(self) -> None: ...

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
