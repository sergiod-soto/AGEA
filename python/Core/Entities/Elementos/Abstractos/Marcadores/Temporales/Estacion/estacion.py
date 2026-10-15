# Core/Entities/Elementos/Abstractos/Marcadores/Temporales/Estacion/estacion.py


from Core.Entities.Elementos.Abstractos.Marcadores.Temporales.marcador_temporal import (
    Marcador_Temporal,
)


class Estacion(Marcador_Temporal):
    """ """

    def __init__(self, tipo: type, id_elemento: int, **kwargs):
        super().__init__(tipo, id_elemento, **kwargs)
