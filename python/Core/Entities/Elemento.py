#
# clase base de las cosas que son un elemento
# los elementos existen en el mundo, pueden o no moverse a cambio de energia y
# pueden interactuar entre ellos en funcion de su presencia en las proximidades
#


class Elemento:

    tipo = None
    area_visibilidad = None  # int, numero de casillas que puede ver a su alrededor
    casilla = (None, None)  # (x,y)

    def __init__(self, tipo, area_visibilidad, casilla: tuple[int, int], rotacion=0):
        self.tipo = tipo
        self.area_visibilidad = area_visibilidad
        self.casilla = casilla
        self.rotacion = rotacion

    def serialize_casilla(self):
        return str({"x": self.casilla[0], "y": self.casilla[1]})

    def serialize_rotacion(self):
        return str(self.rotacion)
