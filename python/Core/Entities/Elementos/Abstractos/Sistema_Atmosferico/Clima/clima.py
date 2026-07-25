from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)


class Clima(Sistema_Atmosferico):
    """
    El clima es la tendencia general de los sistemas atmosfericos.
    """

    def __init__(self, **kwargs):
        super().__init__(Clima, **kwargs)
        self.climas = {}

    def get(self, posicion: tuple[int, int]): ...  # TODO
