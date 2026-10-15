# Core/Entities/Comportamiento/Salud/nutritivo.py

from Core.Entities.Comportamiento.Salud.salud import Salud


class Nutritivo(Salud):
    """
    Recupera energia si se ingiere

    Parametros:

    - valor_nutritivo: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"valor_nutritivo: float"}
    ABSTRACTOS = {}

    def __init__(self, valor_nutritivo: float, **kwargs):
        super().__init__(**kwargs)
        self.valor_nutritivo = valor_nutritivo

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"nutritivo": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"nutritivo": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "valor_nutritivo",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Si un Elemento con Nutricion lo consume, verá esta regenerada.

Atributos:
\tvalor_nutritivo: float,

Métodos:
\t-
        """
