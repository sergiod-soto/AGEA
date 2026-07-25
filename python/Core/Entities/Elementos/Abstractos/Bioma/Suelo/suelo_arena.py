from Core.Entities.Comportamiento.Terreno.arena import Arena
from Core.Entities.Elementos.Abstractos.Bioma.Suelo.suelo import Suelo


class Suelo_Arena(Suelo, Arena):
    def __init__(self):
        super().__init__()
