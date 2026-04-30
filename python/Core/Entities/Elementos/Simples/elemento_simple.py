from Core.Entities.Elementos.elemento import Elemento


class Elemento_Simple(Elemento):

    def __init__(
        self, tipo, tamanho, distancia_visible, casilla: tuple[int, int], rotacion=0
    ):
        self.tipo = tipo
        self.tamanho = tamanho
        self.distancia_visible = distancia_visible
        self.casilla = casilla
        self.rotacion = rotacion

    def serialize_tamanho(self):
        return self.tamanho

    def serialize_distancia_visible(self):
        return self.distancia_visible

    def serialize_casilla(self):
        return str({"x": self.casilla[0], "y": self.casilla[1]})

    def serialize_rotacion(self):
        return self.rotacion % 360
