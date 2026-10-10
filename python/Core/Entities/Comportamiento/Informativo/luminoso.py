from Core.Entities.Comportamiento.Informativo.informativo import Informativo


class Luminoso(Informativo):
    """
    Parametros:

    - distancia: float
    - area: float = 360
    - direccion: float = 0

    Metodos abstractos:

    -
    """

    REQUIERE = {
        "distancia_luz: float",
        "area_luz: float = 360",
        "direccion_luz: float = 0",
    }
    ABSTRACTOS = {}

    def __init__(
        self,
        distancia_luz: float,
        area_luz: float = 360,
        direccion_luz: float = 0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.distancia_luz = distancia_luz
        if area_luz < 0:
            self.area_luz = 0
            self.direccion_luz = 0
        else:
            self.area_luz = area_luz
            self.direccion_luz = direccion_luz

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"luminoso": {}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"luminoso": {}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "distancia_luz",
            "area_luz",
            "direccion_luz",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede emitir luz.

Atributos:
\tdistancia_luz: float,
\tarea_luz: float = 360,
\tdireccion_luz: float = 0,

Métodos:
\t-
        """

    def representar_luminoso(self) -> list[str]:
        """
        Informacion pasada a Unity para representar el Elemento
        """
        representacion = {
            "distancia": self.distancia,
            "area": self.area,
            "direccion": self.direccion,
        }
        return representacion
