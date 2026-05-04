from abc import abstractmethod

from Core.Entities.Comportamiento.Salud.salud import Salud


class Hidratante(Salud):
    """Recupera hidratacion si se ingiere"""

    def __init__(self, valor_hidratacion: float):
        super().__init__()
        self.valor_hidratacion = valor_hidratacion
