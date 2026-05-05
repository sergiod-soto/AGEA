from Core.Entities.Elementos.elemento import Elemento


class Elemento_Simple(Elemento):

    def __init__(
        self, tipo, tamanho: int, casilla: tuple[int, int], capa: int, rotacion: int = 0
    ):
        super().__init__(
            tipo=tipo, tamanho=tamanho, casilla=casilla, capa=capa, rotacion=rotacion
        )

    def serialize_tamanho(self):
        return self.tamanho

    def serialize_capa(self):
        return self.capa

    def serialize_casilla(self):
        return str({"x": self.casilla[0], "y": self.casilla[1]})

    def serialize_rotacion(self):
        return self.rotacion % 360
