# Core/Entities/Comportamiento/Material/liquido.py

from Core.Entities.Comportamiento.Material.material import Material
from Core.Entities.Elementos.elemento import Elemento


class Liquido(Material):
    """
    Parametros:

    -

    Metodos abstractos:

    -
    """

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, disuelto: list[Elemento] = None, **kwargs):
        super().__init__(**kwargs)
        self.disuelto = disuelto or []

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"liquido": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"liquido": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return []

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Indica que el Elemento es Liquido.

Atributos:
\t-

Métodos:
\t-
        """
