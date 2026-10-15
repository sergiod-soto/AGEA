# Core/Entities/Comportamiento/Temporal/latente.py

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
    ABSTRACTOS = {"def tick_comportamiento(self) -> None"}

    def __init__(self, condiciones: list[Condicion], accion_latente: Accion, **kwargs):
        super().__init__(**kwargs)
        self.condiciones = condiciones
        self.accion_latente = accion_latente
        self.activado_latente = True

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"latente": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"latente": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def _campos_internos(cls):
        return {"activado_latente"}

    @abstractmethod
    def tick_comportamiento(self) -> None: ...

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
