from Core.Entities.Comportamiento.Salud.salud import Salud


class Toxico(Salud):
    """Reduce salud si se ingiere"""

    def __init__(self, valor_toxico: float):
        super().__init__()
        self.valor_toxico = valor_toxico
