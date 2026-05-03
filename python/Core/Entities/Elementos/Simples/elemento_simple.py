from Core.Entities.Elementos.elemento import Elemento


class Elemento_Simple(Elemento):

    def __init__(
        self,
        tipo,
        tamanho: float,
        distancia_visible: int,
        casilla: tuple[int, int],
        rotacion: int = 0,
        capa: int = 0,
    ):
        self.tipo = tipo
        self.tamanho = tamanho
        self.distancia_visible = distancia_visible
        self.casilla = casilla
        self.rotacion = rotacion
        self.capa = capa

    def serialize_tamanho(self):
        return self.tamanho

    def serialize_capa(self):
        return self.capa

    def serialize_distancia_visible(self):
        return self.distancia_visible

    def serialize_casilla(self):
        return str({"x": self.casilla[0], "y": self.casilla[1]})

    def serialize_rotacion(self):
        return self.rotacion % 360
