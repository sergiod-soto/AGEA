from Core.Entities.Comportamiento.Terreno.terreno_barro import Embarrado
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo


class Suelo_Barro(Suelo, Embarrado):
    def __init__(self, id_elemento, casilla):
            super().__init__(
                tipo=Suelo_Barro,
                casilla=casilla,
                id_elemento=id_elemento,
            )