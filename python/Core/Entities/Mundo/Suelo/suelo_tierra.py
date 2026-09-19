from Core.Entities.Comportamiento.Terreno.terreno_tierra import Terroso
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Tierra(Suelo, Terroso):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Tierra,
            casilla=casilla,
            id_elemento=id_elemento,
        )
