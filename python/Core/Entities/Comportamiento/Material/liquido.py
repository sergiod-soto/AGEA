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
        datos["comportamientos"][__class__.__name__] = {
            "disuelto": [e.serializar() for e in self.disuelto]
            if self.disuelto
            else []
        }
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"liquido": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        seccion = data.get("comportamientos", {}).get(__class__.__name__, {})
        elementos_data = seccion.get("disuelto", [])
        if elementos_data:
            from Core.Entities.Elementos.registry import reconstruir_elemento

            self.disuelto = [reconstruir_elemento(d, mundo) for d in elementos_data]
        else:
            self.disuelto = []

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
