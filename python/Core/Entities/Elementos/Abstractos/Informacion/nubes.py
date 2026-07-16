from Core.Entities.Elementos.Abstractos.Informacion.informacion import Informacion


class Nubes(Informacion):
    """
    Intensidad de la luz ambiental.

    Depende del ciclo solar, la densidad de nubes, y el
    estado del ciclo lunar.
    """

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(Nubes, **kwargs)
