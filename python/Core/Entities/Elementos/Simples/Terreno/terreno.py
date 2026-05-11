from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple


class Terreno(Elemento_Simple):
    def __init__(
        self,
        casilla: tuple[int, int],
        capa: int = 0,
    ):
        super().__init__(
            Terreno,
            1,
            casilla,
            capa,
            rotacion=0,
        )

    # TODO: terminar de definir Terreno
