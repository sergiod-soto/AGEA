from abc import abstractmethod

from Core.Entities.Comportamiento.Temporal.temporal import Temporal
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.estacion import Estacion


class Estacional(Temporal):
    """
    Parametros:

    - acciones_por_estacion: dict[Estacion, list[Accion]]

    Metodos abstractos:

    -
    """

    REQUIERE = {"acciones_por_estacion: dict[Estacion, list[Accion]]"}
    ABSTRACTOS = {"def on_cambio_estacion(estacion: Estacion) -> None"}

    def __init__(self, acciones_por_estacion: dict[Estacion, list[Accion]], **kwargs):
        super().__init__(**kwargs)
        self.acciones_por_estacion = acciones_por_estacion

    @classmethod
    def _campos_internos(cls):
        return {"acciones_por_estacion"}

    @abstractmethod
    def on_cambio_estacion(estacion: Estacion) -> None: ...
