from Core.Entities.Comportamiento.Fisico.fisico import Fisico


class Flotable(Fisico):
    """
    Parametros:

    -

    Metodos abstractos:

    -
    """

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
