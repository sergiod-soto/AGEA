#
# clase base de las cosas que son un elemento
# los elementos existen en el mundo, pueden o no moverse a cambio de energia y
# pueden interactuar entre ellos en funcion de su presencia en las proximidades
#

from Core.Entities.Comportamiento.comportamiento import Comportamiento


class Elemento(Comportamiento):

    mundo = None

    def __init__(self, tipo: type, capa: int):
        super().__init__()
        self.capa = capa
        self.tipo = tipo
