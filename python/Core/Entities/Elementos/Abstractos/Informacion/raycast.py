from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Raycast(Elemento_Abstracto):
    def __init__(
        self,
        x_origen: int,
        y_origen: int,
        angulo: int,
        distancia_max: float,
        **kwargs,
    ):
        super().__init__(Raycast, **kwargs)

    def resolver(self): ...
