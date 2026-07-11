# Core/Entities/Elementos/Simples/Celda/celda.py
from numpy import uint64

from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple


class Celda(Elemento_Simple):
    def __init__(
        self,
        casilla: tuple[int, int],
        suelo: uint64,
        bot: uint64 = None,
        resto: list[uint64] | None = None,
        capa: int = 0,
    ):
        super().__init__(
            Celda,
            1,
            casilla,
            capa,
            rotacion=0,
        )
        self.suelo = suelo
        self.bot = bot
        self.resto = resto if resto is not None else []

    # TODO: terminar de definir Celda
