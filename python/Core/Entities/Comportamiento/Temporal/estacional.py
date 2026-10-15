# Core/Entities/Comportamiento/Temporal/estacional.py

from abc import abstractmethod

from Core.Entities.Comportamiento.Temporal.temporal import Temporal
from Core.Entities.Elementos.Abstractos.Acciones.accion import Accion
from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.Estacion.estacion import (
    Estacion,
)


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

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"estacional": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"estacional": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def _campos_internos(cls):
        return {"acciones_por_estacion"}

    @abstractmethod
    def on_cambio_estacion(estacion: Estacion) -> None: ...

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "acciones_por_estacion",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento tiene características que dependen de la estación.

Atributos:
\tacciones_por_estacion: dict[Estacion, list[Accion]]

Métodos:
\t-
        """
