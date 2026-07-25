# Core/Entities/Abstractos/Sistema_Atmosferico/Sistema_Primario/temperatura.py

from Core.Entities.Elementos.Abstractos.Sistema_Atmosferico.sistema_atmosferico import (
    Sistema_Atmosferico,
)


class Temperatura(Sistema_Atmosferico):
    def __init__(self, **kwargs):
        super().__init__(Temperatura, **kwargs)


    def actualizar(self): ...  # TODO
