from Core.Entities.Comportamiento.Terreno.terreno import Terreno


class Terreno_Bloqueante(Terreno):
    """
    Terreno que impide el paso, tanto de elementos simples
    como de elementos atmosfericos
    """

    REQUIERE = {}
    ABSTRACTOS = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
