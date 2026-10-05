# Core/Entities/Mundo/Suelo/suelo_limite.py

from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Limite(Suelo):
    '''
    Suelo especial. Es el suelo que se usa como muro impenetrable
    para evitar que nada se salga del mapa.
    '''
    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Limite,
            casilla=casilla,
            id_elemento=id_elemento,
        )
