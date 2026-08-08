from Core.Entities.Comportamiento.Terreno.terreno_grava import Grava
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo


class Suelo_Grava(Suelo, Grava):
    def __init__(self):
        super().__init__()