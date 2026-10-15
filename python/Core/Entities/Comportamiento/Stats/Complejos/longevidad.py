# Core/Entities/Comportamiento/Stats/Complejos/longevidad.py


from Core.Entities.Comportamiento.Stats.stat import Stat
from Core.Entities.Comportamiento.Stats.Complejos.stat_derivado import Stat_Derivado


class Longevidad(Stat_Derivado):
    """ """

    def __init__(self, valores: list[Stat], **kwargs):
        super().__init__(nombre="longevidad", valor=0, **kwargs)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"longevidad": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"longevidad": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    def calcular(self) -> float:
        raise NotImplementedError
