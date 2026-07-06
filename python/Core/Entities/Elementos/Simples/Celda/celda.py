# Core/Entities/Elementos/Simples/Celda/celda.py
from Core.Entities.Comportamiento.Terreno.terreno import Terreno
from Core.Entities.Elementos.Simples.Bot.Bot import Bot
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Elementos.elemento import Elemento


class Celda(Elemento_Simple):
    def __init__(
        self,
        casilla: tuple[int, int],
        suelo: Terreno,
        bot: Bot = None,
        resto: list[Elemento] = [],
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
        self.resto = resto

    # TODO: terminar de definir Celda
