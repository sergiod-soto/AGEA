# Core/Entities/Comportamiento/Stats/Simples/distancia_visual.py


from Core.Entities.Comportamiento.Stats.stat import Stat


class Distancia_Visual(Stat):
    def __init__(self, valor: int):
        # TODO: formula que acepte la distancia maxima del mundo
        # y el valor y retorne la distancia maxima para ese bot
        super().__init__(
            nombre="distancia_visual",
            valor=valor,
        )

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"distancia_visual": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"distancia_visual": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
