from Core.Entities.Comportamiento.Terreno.piedra import Piedra
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo


class Suelo_Piedra(Suelo, Piedra):
    def __init__(self):
        super().__init__()