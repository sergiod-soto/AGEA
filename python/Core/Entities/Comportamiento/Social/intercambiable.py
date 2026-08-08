from Core.Entities.Comportamiento.Social.social import Social


class Intercambiable(Social):
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
