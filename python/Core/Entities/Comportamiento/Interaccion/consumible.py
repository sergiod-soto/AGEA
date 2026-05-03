from abc import abstractmethod

from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.elemento import Elemento


class Consumible(Interaccion):
    def __init__(self, valor_nutritivo: float = None, valor_hidratacion: float = None):
        super().__init__()
        self.valor_nutritivo = valor_nutritivo
        self.valor_hidratacion = valor_hidratacion

    @abstractmethod
    def consumir(self, por: Elemento): ...
