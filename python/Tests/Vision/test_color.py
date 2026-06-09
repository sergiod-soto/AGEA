from dataclasses import dataclass

from Core.Entities.Comportamiento.Informativo.color import Color
from Core.Entities.Elementos.Simples.elemento_simple import Elemento_Simple


@dataclass
class FakeElemento(Elemento_Simple, Color):

    def __init__(self, **kwargs):

        self.rgb_base = [10.0, 10.0, 10.0]

        super().__init__(FakeElemento, **kwargs)


elemento = FakeElemento()

# def test_color():
elemento.iluminar_con_color([0.0, 10.0, 50.0], 50)
print("intensidad: " + str(elemento.intensidad))
