# Core/Entities/Elementos/Simples/elemento_simple.py

from Core.Entities.Elementos.elemento import Elemento


class Elemento_Simple(Elemento):
    """
    - tipo,
    - tamanho: int,
    - casilla: tuple[int, int],
    - capa: int,
    - rotacion: float = 0,
    - resistencia_viento: float = 0.0,
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
        self.resistencia_viento = resistencia_viento

    # --- Hooks por campo (se mantienen): conversión de formato ---
    # serializar_X: valor interno -> valor serializable.
    # deserializar_X: lo inverso (también lo usa Elemento.aplicar_patch).

    def serializar_tamanho(self):
        return self.tamanho

    def serializar_casilla(self):
        return {"x": self.casilla[0], "y": self.casilla[1]}

    def deserializar_casilla(self, value):
        self.casilla = (value["x"], value["y"])

    # 'rotacion' se normaliza a [0, 360) al serializar.
    def serializar_rotacion(self):
        return self.rotacion % 360

    # (typo corregido: antes "serializar_resistenca_viento")
    def serializar_resistencia_viento(self):
        return self.resistencia_viento

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
        self.resistencia_viento = data["resistencia_viento"]
