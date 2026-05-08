from typing import Callable

from Core.Entities.Comportamiento.comportamiento import Comportamiento
from Core.Mundo.mundo import Mundo


class Elemento(Comportamiento):
    """
    Clase base de las cosas que son un elemento, ya sea simple, complejo o abstracto.


    Los elementos existen en el mundo, pueden o no moverse a cambio de energia y
    pueden interactuar entre ellos en funcion de su presencia en las proximidades
    """

    mundo: Mundo = None

    def __init__(self, tipo: type, capa: int):
        super().__init__()
        self._suscripciones: list[tuple[str, Callable]] = []

        self.capa = capa
        self.tipo = tipo

    def _suscribir_evento(self, tipo: str, callback: Callable) -> None:
        Elemento.mundo.bus.suscribir(tipo, callback)
        self._suscripciones.append((tipo, callback))

    def eliminar(self) -> None:
        for tipo, callback in self._suscripciones:
            Elemento.mundo.bus.desuscribir(tipo, callback)
        self._suscripciones.clear()
