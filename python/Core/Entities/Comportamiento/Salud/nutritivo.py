from Core.Entities.Comportamiento.Stats.Simples.salud import Salud


class Nutritivo(Salud):
    """
    Recupera energia si se ingiere

    Parametros:

    - valor_nutritivo: float
    
    Metodos abstractos:

    -
    """

    def __init__(self, valor_nutritivo: float,**kwargs):
        super().__init__(**kwargs)
        self.valor_nutritivo = valor_nutritivo

