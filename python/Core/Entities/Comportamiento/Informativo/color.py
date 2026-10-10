# Core/Entities/Comportamiento/Informativo/color.py

from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Exceptions.Bot.comportamientos_exceptions import Transparencia_Incorrecta


class Color(Comportamiento):
    """
    Color del Elemento en RGB

    Parametros:

    - rgb_base: tuple[float, float, float]
    - transparente: float = 0

    Metodos abstractos:

    -
    """

    REQUIERE = {"rgb_base: tuple[float, float, float]", "transparente: float = 0"}
    ABSTRACTOS = {}

    def __init__(
        self,
        rgb_base: tuple[float, float, float],
        transparente: float = 0,
        **kwargs,
    ):
        if transparente < 0 or transparente > 1:
            raise Transparencia_Incorrecta(transparente)

        super().__init__(**kwargs)
        self.rgb_base = rgb_base  # color base: proporcion, inmutable
        self.transparente = transparente  # % de tansparencia
        self.modificador = [
            rgb_base[0] / 255,
            rgb_base[1] / 255,
            rgb_base[2] / 255,
        ]  # rbg_base normalizado 0.0 - 1.0
        self.rgb_actual = [0.0, 0.0, 0.0]  # color que refleja

    @classmethod
    def _campos_internos(cls):
        return {"modificador", "rgb_actual"}

    def iluminar_con_color(
        self,
        color_luz: tuple[float, float, float],
    ):
        """
        Modifica el color (e intensidad) que refleja
        el elemento en base al color e intensidad con el que es iluminado
        """

        max_canal_entrante = 0

        if color_luz[0] > max_canal_entrante:
            max_canal_entrante = color_luz[0]

        if color_luz[1] > max_canal_entrante:
            max_canal_entrante = color_luz[1]

        if color_luz[2] > max_canal_entrante:
            max_canal_entrante = color_luz[2]

        if max_canal_entrante == 0:
            # intensidad == 0
            return
        # modifico la luz entrante en funcion al color base
        color_luz[0] = self.modificador[0] * color_luz[0]
        color_luz[1] = self.modificador[1] * color_luz[1]
        color_luz[2] = self.modificador[2] * color_luz[2]

        self.rgb_actual[0] = self.rgb_actual[0] + color_luz[0]
        self.rgb_actual[1] = self.rgb_actual[1] + color_luz[1]
        self.rgb_actual[2] = self.rgb_actual[2] + color_luz[2]

    def get_rgb_normalizado(self) -> tuple[float, float, float]:
        """
        Retorna el RGB de la luz total reflejada,
        normalizada a 255 para representacion, no uso.
        """

        rgb = self.rgb_actual
        max = 0

        if rgb[0] > max:
            max = rgb[0]

        if rgb[1] > max:
            max = rgb[1]

        if rgb[2] > max:
            max = rgb[2]

        rgb[0] = rgb[0] / max * 255
        rgb[1] = rgb[1] / max * 255
        rgb[2] = rgb[2] / max * 255

        return rgb

    # --- Cadena serializar / representar / deserializar ---

    def serializar(self) -> dict:
        # Fidelidad completa: incluye el estado interno (modificador,
        # rgb_actual), que no son parámetros del __init__.
        datos = super().serializar()
        datos["comportamientos"][__class__.__name__] = {
            "rgb_base": self.rgb_base,
            "transparente": self.transparente,
            "modificador": self.modificador,
            "rgb_actual": self.rgb_actual,
        }
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        """Informacion pasada a Unity: solo lo necesario para dibujar."""
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["comportamientos"][__class__.__name__] = {
                "rgb_base": self.rgb_base,
                "transparente": self.transparente,
            }
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        s = data["comportamientos"][__class__.__name__]
        self.rgb_base = s["rgb_base"]
        self.transparente = s["transparente"]
        self.modificador = s["modificador"]
        self.rgb_actual = s["rgb_actual"]

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "rgb_base",
            "transparente",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento, al ser iluminado, modifica el valor de la luz que refleja.

Atributos:
\trgb_base: tuple[float, float, float],
\ttransparente: float = 0,

Métodos:
\tiluminar_con_color(self, color_luz: tuple[float, float, float])
\t--------------------------------------
\tModifica el color (e intensidad) que refleja
\tel elemento en base al color e intensidad con el que es iluminado

\tget_rgb_normalizado(self) -> tuple[float, float, float]
\t--------------------------------------
\tRetorna el RGB de la luz total reflejada
\tnormalizada a 255 para representacion, no uso.
        """
