from abc import abstractmethod

from Core.Entities.Comportamiento.Temporal.temporal import Temporal
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Condiciones.condicion import Condicion


class Latente(Temporal):
    """
    No hace nada mientras no se den las condiciones correctas,
    como una semilla hasta que se entierra
    """

    def __init__(
        self,
        condiciones: list[Condicion],
        accion_latente: Accion,
        activado_latente: bool = True,
    ):
        super().__init__()
        self.condiciones = condiciones
        self.accion_latente = accion_latente
        self.activado_latente = activado_latente

        @abstractmethod
        def tick(self) -> None: ...
