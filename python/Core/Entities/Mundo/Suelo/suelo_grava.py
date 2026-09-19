from Core.Entities.Comportamiento.Terreno.terreno_grava import Gravoso
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Grava(Suelo, Gravoso):
    def __init__(self, id_elemento, casilla):
            super().__init__(
                tipo=Suelo_Grava,
                casilla=casilla,
                id_elemento=id_elemento,
            )