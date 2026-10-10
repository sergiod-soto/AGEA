# Core/Entities/Comportamiento/Fisico/volumen.py

from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Volumen(Fisico):
    """
    (cm3)

    Parametros:

    - volumen: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"volumen: float"}
    ABSTRACTOS = {}

    def __init__(self, volumen: float, **kwargs):
        super().__init__(**kwargs)
        self.volumen = volumen

    # --- Cadena serializar / representar / deserializar ---

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "volumen": {"volumen": self.volumen}
        }
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity para representar el Elemento."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {
                "volumen": {"volumen": self.volumen}
            }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.volumen = data["comportamientos"][__class__.__name__]["volumen"]

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "volumen",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento tiene volumen espacial.

Atributos:
\tvolumen: float

Métodos:
\t-
        """
