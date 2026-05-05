from Core.Entities.Comportamiento.Salud.salud import Salud


class Toxico(Salud):
    """
    Reduce salud si se ingiere
    
    Parametros:
    
    - valor_toxico: float
    """

    def __init__(self, valor_toxico: float):
        super().__init__()
        self.valor_toxico = valor_toxico
