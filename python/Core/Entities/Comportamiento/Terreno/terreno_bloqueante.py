from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class Terreno_Bloqueante(Terreno):
    """
    Terreno que impide el paso, tanto de elementos simples
    como de elementos atmosfericos
    """

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"terreno_bloqueante": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"terreno_bloqueante": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
