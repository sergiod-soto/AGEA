from Core.Entities.Comportamiento.Stats.Simples.salud import Salud


class Toxico(Salud):
    """
    Reduce salud si se ingiere
    
    Parametros:
    
    - valor_toxico: float
    """

    def __init__(self, valor_toxico: float,**kwargs):
        super().__init__(**kwargs)
        self.valor_toxico = valor_toxico
