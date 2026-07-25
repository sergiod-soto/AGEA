from Core.Entities.Comportamiento.Terreno.charco import Charco
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo


class Suelo_Charco(Suelo, Charco):
    def __init__(self):
        super().__init__()