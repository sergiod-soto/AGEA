from abc import abstractmethod

from Core.Entities.Comportamiento.Temporal.temporal import Temporal
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Latente(Temporal):
    """
    No hace nada mientras no se den las condiciones correctas,
    como una semilla hasta que se entierra.

    Parametros:

    - condiciones: list[tuple(Condicion, Accion)]

    Metodos abstractos:

    - tick() -> None
    """

    REQUIERE = {
        "condiciones: list[Condicion]",
        "accion_latente: Accion",
    }
    ABSTRACTOS = {"def tick(self) -> None"}

    def __init__(self, condiciones: list[Condicion], accion_latente: Accion, **kwargs):
        super().__init__(**kwargs)
        self.condiciones = condiciones
        self.accion_latente = accion_latente
        self.activado_latente = True

    @classmethod
    def _campos_internos(cls):
        return {"activado_latente"}

    @abstractmethod
    def tick(self) -> None: ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return """
•El Elemento tiene características que se activan al darse determinadas condiciones.

Atributos:
\tcondiciones: list[tuple(Condicion, Accion)]

Métodos:
\t@abstractmethod tick(self) -> None
\t--------------------------------------
\tComputa el siguiente tick.
            """
