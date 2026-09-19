from Core.Entities.Comportamiento.Terreno.terreno_cesped import Hervoso
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Cesped(Suelo, Hervoso):
    def __init__(self, id_elemento, casilla):
            super().__init__(
                tipo=Suelo_Cesped,
                casilla=casilla,
                id_elemento=id_elemento,
            )