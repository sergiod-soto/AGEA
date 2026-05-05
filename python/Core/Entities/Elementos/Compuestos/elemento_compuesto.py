from Core.Entities.Elementos.elemento import Elemento


class Elemento_Compuesto(Elemento):
    def __init__(self, tipo: type, capa):
        super().__init__(tipo, capa)
