from abc import abstractmethod

from Core.Entities.Comportamiento.Salud.salud import Salud


class Medicinal(Salud):
    """Recupera salud si se ingiere"""

    def __init__(self, valor_medicinal: float):
        super().__init__()
        self.valor_medicinal = valor_medicinal

  