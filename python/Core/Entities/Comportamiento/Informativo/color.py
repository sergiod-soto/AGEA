from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Color(Comportamiento):
    def __init__(self, rgb: tuple[int, int, int]):
        super().__init__()
        self.rgb = rgb
