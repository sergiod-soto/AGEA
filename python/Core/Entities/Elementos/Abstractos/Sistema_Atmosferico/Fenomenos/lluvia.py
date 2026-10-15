# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Fenomenos/lluvia.py

from Core.Entities.Elementos.Abstractos.Informacion.informacion import Informacion


class Lluvia(Informacion):
    """
    Estado Sector de lluvia.
    """

    def __init__(self, **kwargs):
        super().__init__(Lluvia, **kwargs)
