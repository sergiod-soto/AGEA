from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Flotable(Fisico):
    """
    Etiqueta
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flotable: bool = True
