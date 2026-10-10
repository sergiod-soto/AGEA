# Core/Entities/Comportamiento/Fisico/peso.py

from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Peso(Fisico):
    """
    (kilos.gramos)

    NO indica que algo pese mucho, si no que tiene masa

    Parametros:

    - peso: float

    Metodos abstractos:

    -
    """

    REQUIERE = {"peso: float"}
    ABSTRACTOS = {}

    def __init__(self, peso: float, **kwargs):
        super().__init__(**kwargs)
        self.peso = peso

    # --- Cadena serializar / representar / deserializar ---
    # Las claves de la sección DEBEN coincidir con los parámetros del
    # __init__: reconstruir_elemento() usa la sección como kwargs de
    # Comportamiento.anhadir() cuando el comportamiento hay que añadirlo.

    def serializar(self) -> dict:
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {"peso": {"peso": self.peso}}
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        # Unity no necesita el peso para dibujar; solo se envía si el
        # llamador lo pide en `incluir` (o con incluir=None, que es todo).
        # Si no debe salir nunca, basta con borrar este método.
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {"peso": {"peso": self.peso}}
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.peso = data["comportamientos"][__class__.__name__]["peso"]

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "peso",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•Peso es la masa del elemento.

Atributos:
\tpeso: float

Métodos:
\t-
            """
