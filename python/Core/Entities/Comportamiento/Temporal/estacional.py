from Core.Entities.Comportamiento.Temporal.temporal import Temporal
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Marcadores.Tiempo.estacion import Estacion


class Estacional(Temporal):

    def __init__(self, acciones_por_estacion: dict[Estacion, list[Accion]]):
        super().__init__()
        self.acciones_por_estacion = acciones_por_estacion

    def on_cambio_estacion(estacion: Estacion) -> None: ...
