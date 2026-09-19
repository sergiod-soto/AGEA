from Core.Entities.Mundo.Suelo.suelo import Suelo


class Suelo_Muro(Suelo):
    """
    Suelo que bloquea, ya sean elementos o eventos climatologicos
    """

    def __init__(self, id_elemento, casilla):
        super().__init__(
            tipo=Suelo_Muro,
            casilla=casilla,
            id_elemento=id_elemento,
        )
