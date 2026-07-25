from Core.Entities.Comportamiento.Terreno.cesped import Cesped
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo


class Suelo_Cesped(Suelo, Cesped):
    def __init__(self):
        super().__init__()