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
            Elemento.Flags.RESISTENCIA_VIENTO_CACHEABLE,  #
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

    def serializar_tamanho(self):
        return self.tamanho

    def serializar_casilla(self):
        return {"x": self.casilla[0], "y": self.casilla[1]}

    def deserializar_casilla(self, value):
        self.casilla = (value["x"], value["y"])

    # 'rotacion' se normaliza a [0, 360) al serializar.
    def serializar_rotacion(self):
        return self.rotacion % 360

    def serializar_resistenca_viento(self):
        return self.resistencia_viento

    def serializar_elemento_simple(self) -> dict:
        serializacion = self.serializar_elemento()
        s_simple = {
            "tipo_elemento": "elemento_simple",
            "tamanho": self.serializar_tamanho(),
            "casilla": self.serializar_casilla(),
            "rotacion": self.serializar_rotacion(),
            "resistencia_viento": self.serializar_resistenca_viento(),
        }
        serializacion.update(s_simple)
        return serializacion
