from Core.Entities.Comportamiento.Stats.Informacion.informacion import Informacion


class Raycast(Informacion):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(Raycast, **kwargs)
