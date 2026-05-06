from abc import abstractmethod

from Core.Entities.Comportamiento.Stats.Simples.salud import Salud


class Hidratante(Salud):
    """
    Recupera hidratacion si se ingiere
    
    Parametros:
    
    - valor_hidratacion: float
    """

    def __init__(self, valor_hidratacion: float,**kwargs):
        super().__init__(**kwargs)
        self.valor_hidratacion = valor_hidratacion
