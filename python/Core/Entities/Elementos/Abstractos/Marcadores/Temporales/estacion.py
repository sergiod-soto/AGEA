from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)


class Estacion(Marcador_Temporal):
    def __init__(self, **kwargs):
        super().__init__(Estacion, **kwargs)
