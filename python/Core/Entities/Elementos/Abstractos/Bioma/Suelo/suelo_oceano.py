from Core.Entities.Comportamiento.Terreno.terreno_oceano import Oceanico
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo


class Suelo_Oceano(Suelo, Oceanico):
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Oceano,
            casilla=casilla,
            id_elemento=id_elemento,
        )
