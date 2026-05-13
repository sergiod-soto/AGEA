from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Mundo.mundo import Mundo


class Elemento(Comportamiento):
    """
    Clase base de las cosas que son un elemento, ya sea simple, complejo o abstracto.


    Los elementos existen en el mundo, pueden o no moverse a cambio de energia y
    pueden interactuar entre ellos en funcion de su presencia en las proximidades
    """

    mundo: Mundo = None

    def __init__(self, tipo: type, capa: int, **kwargs):
        super().__init__(**kwargs)

        self.capa = capa
        self.tipo = tipo

    def eliminar(self): ...  # Completar Eliminar Elemento
