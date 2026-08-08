from Core.Entities.Comportamiento.Terreno.terreno_barro import Barro
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo


class Suelo_Barro(Suelo, Barro):
    def __init__(self):
        super().__init__()