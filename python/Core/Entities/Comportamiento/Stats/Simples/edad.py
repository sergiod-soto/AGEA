# Core/Entities/Comportamiento/Stats/Simples/edad.py

from Core.Entities.Comportamiento.Stats.stat import Stat


class Edad(Stat):
    def __init__(self, valor: int, edad_adulta: int):
        super().__init__(nombre="edad", valor=valor)
        self.edad_adulta = edad_adulta

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"edad": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"edad": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
