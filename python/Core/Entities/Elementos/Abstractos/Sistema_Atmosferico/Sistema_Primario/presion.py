from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)


class Presion(Sistema_Atmosferico):

    def __init__(self, **kwargs):
        super().__init__(Presion, **kwargs)

    def get(self, posicion: tuple[int, int]): ...  # TODO
