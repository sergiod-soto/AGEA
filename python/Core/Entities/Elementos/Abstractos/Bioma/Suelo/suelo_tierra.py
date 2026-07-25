from Core.Entities.Comportamiento.Terreno.tierra import Tierra
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo


class Suelo_Tierra(Suelo, Tierra):
    def __init__(self):
        super().__init__()
