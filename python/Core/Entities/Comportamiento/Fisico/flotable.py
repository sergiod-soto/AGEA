# Core/Entities/Comportamiento/Fisico/flotable.py

from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Flotable(Fisico):
    """
    Parametros:

    -

    Metodos abstractos:

    -
    """

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"flotable": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"flotable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return """
•El Elemento mantiene capa > 0 en terreno de agua.

Atributos:
\t-

Métodos:
\t-
        """
