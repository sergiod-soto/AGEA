from Core.Entities.Elementos.Simples.Comida.comida import Comida


# TODO: definir ingrediente
class Ingrediente(Comida):
    def __init__(self, tipo, casilla, capa):
        super().__init__(tipo, casilla, capa)
