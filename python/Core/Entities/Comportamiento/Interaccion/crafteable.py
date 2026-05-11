from Core.Entities.Comportamiento.Interaccion.interaccion import Interaccion
from Core.Entities.Elementos.Abstractos.Recetas.receta import Receta


class Crafteable(Interaccion):
    """
    Parametros:

    - receta: Receta

    Metodos abstractos:

    -
    """

    def __init__(self, receta: Receta, **kwargs):
        super().__init__(**kwargs)
        self.receta = receta
        for ingrediente in self.receta.ingredientes:
            ingrediente.incluir_en_receta(self.receta)
