# Core/Entities/Comportamiento/Stats/Simples/deteccion.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Deteccion(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="deteccion", valor=valor)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"deteccion": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"deteccion": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
