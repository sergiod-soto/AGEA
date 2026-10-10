# Core/Entities/Comportamiento/Stats/Informacion/id.py

# Stat informativo: incluso sin valor por defecto sensato (cada Bot
# necesita un id distinto), sigue el mismo patron que los demas stats
# para que Tiene_Stats no tenga que distinguir "informativo" de "simple".
from Core.Entities.Comportamiento.Stats.stat import Stat


class ID(Stat):
    def __init__(self, valor):
        super().__init__(nombre="id", valor=valor)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"id": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"id": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
