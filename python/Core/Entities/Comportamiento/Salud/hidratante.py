from Core.Entities.Comportamiento.Salud.salud import Salud


class Hidratante(Salud):
    """
    Recupera hidratacion si se ingiere

    Parametros:

    - valor_hidratacion: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"valor_hidratacion: float"}
    ABSTRACTOS = {}

    def __init__(self, valor_hidratacion: float, **kwargs):
        super().__init__(**kwargs)
        self.valor_hidratacion = valor_hidratacion

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"hidratante": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"hidratante": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "valor_hidratacion",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Si es consumido por un Elemento con el atributo Hidratacion, este la verá regenerada.

Atributos:
\tvalor_hidratacion: float,

Métodos:
\t-
        """
