# Core/Entities/Mundo/Suelo/suelo_charco.py

from Core.Entities.Comportamiento.Terreno.encharcado import Encharcado
from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Charco(Suelo, Encharcado):
    def __init__(self, id_elemento, casilla):
            super().__init__(
                tipo=Suelo_Charco,
                casilla=casilla,
                id_elemento=id_elemento,
            )