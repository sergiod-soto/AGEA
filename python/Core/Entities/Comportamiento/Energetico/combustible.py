from Core.Entities.Comportamiento.Energetico.energetico import Energetico


class Combustible(Energetico):
    """
    No se mira la parte de arder, si no la parte energetica.

    Util para poder crear cosas que almacenen energia, desligado del
    proceso de combustion

    Parametros:

    - energia_maxima: float,
    - ratio_emision: float,
    - energia_actual: float = None,
    - ratio_recarga: float = 0.0

    Metodos abstractos:

    -
    """

    REQUIERE = {
        "energia_maxima: float",
        "ratio_emision: float",
        "ratio_recarga: float = 0.0",
    }
    ABSTRACTOS = {}

    def __init__(
        self,
        energia_maxima: float,
        ratio_emision: float,
        ratio_recarga: float = 0.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.energia_maxima = energia_maxima
        self.ratio_emision = ratio_emision
        self.energia_actual = energia_maxima
        self.ratio_recarga = ratio_recarga

    @classmethod
    def _campos_internos(cls):
        return {"energia_actual"}

    def gastar(self, cantidad: float) -> float:
        if cantidad > self.ratio_emision:
            cantidad = self.ratio_emision

        if self.energia_actual >= cantidad:
            self.energia_actual -= cantidad
            return cantidad
        else:
            cantidad = self.energia_actual
            self.energia_actual = 0.0
            return cantidad

    def cargar(self, cantidad: float):
        if cantidad > self.ratio_recarga:
            cantidad = self.ratio_recarga

        self.energia_actual += cantidad

        if self.energia_actual > self.energia_maxima:
            self.energia_actual = self.energia_maxima

    @classmethod
    def campos_para_creacion(cls) -> list[str]:
        return [
            "energia_maxima",
            "ratio_emision",
            "energia_actual",
            "ratio_recarga",
        ]

    @classmethod
    def ayuda_creacion(cls) -> str:
        return """
•El Elemento puede ser usado como fuente de energia (no implica combustión).

Atributos:
\tenergia_maxima: float,
\tratio_emision: float,
\tenergia_actual: float = None,
\tratio_recarga: float = 0.0

Métodos:
\tgastar(self, cantidad: float) -> float
\t--------------------------------------
\tConsume carga de energía.

\tcargar(self, cantidad: float)
\t--------------------------------------
\tRecarga energía.
            """
