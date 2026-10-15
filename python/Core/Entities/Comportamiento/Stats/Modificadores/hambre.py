# Core/Entities/Comportamiento/Stats/Modificadores/hmabre.py

from Core.Entities.Comportamiento.Stats.Modificadores.modificador import Modificador


class Hambre(Modificador):
    def __init__(self, valor: float = 0.0, **kwargs):
        super().__init__("hambre", valor, **kwargs)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"hambre": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"hambre": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
