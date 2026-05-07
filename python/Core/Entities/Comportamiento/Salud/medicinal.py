from abc import abstractmethod

from Core.Entities.Comportamiento.Stats.Simples.salud import Salud


class Medicinal(Salud):
    """
    Recupera salud si se ingiere

    Parametros:

    - valor_medicinal: float

    Metodos abstractos:

    -
    """

    def __init__(self, valor_medicinal: float, **kwargs):
        super().__init__(**kwargs)
        self.valor_medicinal = valor_medicinal
