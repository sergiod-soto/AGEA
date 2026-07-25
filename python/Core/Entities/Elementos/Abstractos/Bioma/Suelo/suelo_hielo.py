from Core.Entities.Comportamiento.Terreno.hielo import Hielo
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo


class Suelo_Hielo(Suelo, Hielo):
    def __init__(self):
        super().__init__()