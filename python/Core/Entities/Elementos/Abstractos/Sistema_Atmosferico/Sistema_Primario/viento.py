from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)


class Viento(Sistema_Atmosferico):
    def __init__(self, **kwargs):
        super().__init__(Viento, **kwargs)

    def get(self, posicion: tuple[int, int]): ...  # TODO
