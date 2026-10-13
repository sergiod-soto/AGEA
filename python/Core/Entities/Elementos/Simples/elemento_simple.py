# Core/Entities/Elementos/Simples/elemento_simple.py

from Core.Entities.Elementos.elemento import Elemento


class Elemento_Simple(Elemento):
    """
    Elemento que ocupa una casilla del mundo.

    Parametros:
    - tipo, id_elemento, capa: se pasan al Elemento base
    - tamanho: float
    - casilla: tuple[int, int]
    - rotacion: float = 0 (grados; se normaliza a [0, 360) al serializar)
    - resistencia_viento: float = 0.0, en [0, 1]
      (0 = no frena el viento, 1 = lo bloquea del todo)
    """

    FLAGS_DISPONIBLES = frozenset(
        {
            Elemento.Flags.RESISTENCIA_VIENTO_CACHEABLE,
        }
    )

    def __init__(
        self,
        tipo,
        id_elemento,
        tamanho: float,
        casilla: tuple[int, int],
        capa: int,
        rotacion: float = 0,
        resistencia_viento: float = 0.0,
        **kwargs,
    ):
        super().__init__(
            tipo=tipo,
            capa=capa,
            id_elemento=id_elemento,
            **kwargs,
        )
        self.tamanho = tamanho
        self.casilla = casilla
        self.rotacion = rotacion
        self.resistencia_viento = self._validar_resistencia_viento(resistencia_viento)

    @staticmethod
    def _validar_resistencia_viento(valor: float) -> float:
        """
        Fuera de [0, 1] el modelo multiplicativo del viento daría pasos
        libres negativos o >1 y fallaría lejos del origen del error. Se
        comprueba aquí (el `not` también rechaza NaN).
        """
        if not 0.0 <= valor <= 1.0:
            raise ValueError(
                f"resistencia_viento debe estar en [0, 1]; recibido {valor!r}"
            )
        return valor

    # --- Hooks por campo: conversión de formato ---
    # serializar_X: valor interno -> valor serializable.
    # deserializar_X: lo inverso (también lo usa Elemento.aplicar_patch).

    def serializar_tamanho(self):
        return self.tamanho

    def serializar_casilla(self):
        return {"x": self.casilla[0], "y": self.casilla[1]}

    def deserializar_casilla(self, value):
        self.casilla = (value["x"], value["y"])

    def serializar_rotacion(self):
        return self.rotacion % 360

    def serializar_resistencia_viento(self):
        return self.resistencia_viento

    def deserializar_resistencia_viento(self, value) -> None:
        # Hook con validación: un patch de consola (modificar_elemento)
        # pasa por aquí en vez de un setattr que se saltaría el rango.
        self.resistencia_viento = self._validar_resistencia_viento(value)

    # --- Cadena serializar / representar / deserializar ---

    def serializar(self) -> dict:
        datos = super().serializar()
        datos.update(
            {
                "tamanho": self.serializar_tamanho(),
                "casilla": self.serializar_casilla(),
                "rotacion": self.serializar_rotacion(),
                "resistencia_viento": self.serializar_resistencia_viento(),
            }
        )
        return datos

    def representar(self, incluir: list[str] | None = None) -> dict:
        datos = super().representar(incluir)
        if self._incluido(incluir, __class__):
            datos["elemento"].update(
                {
                    "tipo_elemento": "elemento_simple",
                    "tamanho": self.serializar_tamanho(),
                    "casilla": self.serializar_casilla(),
                    "rotacion": self.serializar_rotacion(),
                    "resistencia_viento": self.serializar_resistencia_viento(),
                }
            )
        return datos

    def deserializar(self, data: dict, mundo=None) -> None:
        super().deserializar(data, mundo)
        self.tamanho = data["tamanho"]
        self.deserializar_casilla(data["casilla"])
        self.rotacion = data["rotacion"]
        self.deserializar_resistencia_viento(data["resistencia_viento"])
