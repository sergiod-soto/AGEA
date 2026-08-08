# Core/Entities/Elementos/elemento_test.py

from Core.Entities.Comportamiento.Fisico.peso import Peso
from Core.Entities.Comportamiento.comportamiento_test import Comportamiento_Test
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple
from Core.Entities.Comportamiento.comportamiento import Comportamiento

comportamientos = Comportamiento.declarar_comportamientos(
    Comportamiento_Test,
    Peso,
)


class Elemento_Test(Elemento_Simple, comportamientos):

    def __init__(
        self,
        casilla: tuple[int, int],
        id_elemento,
        # Peso:
        peso: float,
        **kwargs
    ):
        if peso < 0:
            peso = 0
        super().__init__(
            tipo=Elemento_Test,
            id_elemento=id_elemento,
            tamanho=1,
            casilla=casilla,
            capa=1,
            # Peso:
            peso=peso,
            **kwargs
        )
