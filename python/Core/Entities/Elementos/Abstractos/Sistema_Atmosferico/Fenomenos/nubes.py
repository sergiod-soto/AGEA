from Core.Entities.Elementos.Abstractos.Informacion.informacion import Informacion


class Nubes(Informacion):
    """
    Estado GLOBAL de las nubes. Su intensidad depende de la posicion.
    """

    def __init__(self, **kwargs):
        super().__init__(Nubes, **kwargs)
