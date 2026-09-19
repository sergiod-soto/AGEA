from Core.Entities.Comportamiento.Terreno.terreno_hielo import Helado
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Hielo(Suelo, Helado):
    def __init__(self, id_elemento, casilla):
            super().__init__(
                tipo=Suelo_Hielo,
                casilla=casilla,
                id_elemento=id_elemento,
            )