# Core/Entities/Elementos/Abstractos/Informacion/informacion.py

from Core.Entities.Elementos.Abstractos.elemento_abstracto import Elemento_Abstracto


class Informacion(Elemento_Abstracto):
    """ """

    def __init__(self, tipo: type, id_elemento: int, **kwargs):
        super().__init__(tipo, id_elemento, **kwargs)
