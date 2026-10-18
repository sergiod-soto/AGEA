# Core/Entities/Comportamiento/Terreno/oceanico.py

from Core.Entities.Comportamiento.Terreno.acuoso import Acuoso


class Oceanico(Acuoso):
    """
    Oceanico hereda de acuoso, que a su vez hereda de Terreno, por lo que
    este es, de momento, el unico comportamiento de un terreno que no
    hereda directamente de Comportamiento.Terreno.terreno.Terreno
    """

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"oceanico": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"oceanico": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
