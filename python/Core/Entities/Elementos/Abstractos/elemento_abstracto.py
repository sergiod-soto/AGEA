from Core.Entities.Elementos.elemento import Elemento


class Elemento_Abstracto(Elemento):

    def __init__(self, tipo: type):
        super().__init__(tipo=tipo, capa=0)
