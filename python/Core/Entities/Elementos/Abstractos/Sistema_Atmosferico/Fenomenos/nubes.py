# Core/Entities/Elementos/Abstractos/Sistema_Atmosferico/Fenomenos/nubes.py


from Core.Entities.Elementos.Abstractos.Informacion.informacion import Informacion


class Nubes(Informacion):
    """
    Estado Sector de las nubes.
    """

    def __init__(self, **kwargs):
        super().__init__(Nubes, **kwargs)
