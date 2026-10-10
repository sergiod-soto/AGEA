from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.Abstractos.Recetas.receta import Receta


class Crafteable(Interaccion):
    """
    Parametros:

    - receta: Receta

    Metodos abstractos:

    -
    """

    REQUIERE = {"receta: Receta"}
    ABSTRACTOS = {}

    def __init__(self, receta: Receta, **kwargs):
        super().__init__(**kwargs)
        self.receta = receta

        for ingrediente in self.receta.ingredientes:
            ingrediente.incluir_en_receta(self.receta)

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"crafteable": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"crafteable": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "peso",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser generado siguiendo una receta.

Atributos:
\treceta: Receta

Métodos:
\t-
        """
