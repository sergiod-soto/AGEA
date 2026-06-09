from dataclasses import dataclass

from Core.Entities.Comportamiento.Informativo.color import Color
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple


@dataclass
class FakeElemento(Elemento_Simple, Color):

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(
            tipo=FakeElemento,
            tamanho=1,
            casilla=(0, 0),
            capa=1,
            rgb_base=[127.5, 0, 255],
            transparente=0.5,
            **kwargs,
        )


elemento = FakeElemento()

# def test_color():
elemento.iluminar_con_color([240, 10, 0])
elemento.iluminar_con_color([20, 10, 10])

print("rgb: " + str(elemento.rgb_actual))
