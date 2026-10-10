# Core/Entities/Comportamiento/Stats/Simples/edad_adulta.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Edad_Adulta(Stat):
    def __init__(self, valor: int):
        super().__init__(nombre="edad_adulta", valor=valor)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"edad_adulta": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"edad_adulta": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
