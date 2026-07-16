#Infraestructura/Gestores/Mundo/Bus_Eventos/bus.py
from typing import Callable
import weakref


class BusEventos:
    """
    Clase encargada de gestionar los eventos.

    Ejemplo:

    - El comportamiento termico comprueba si algo ha cambiado de temperatura.
    En caso de asi ser, llama a emitir el evento 'temperatura_cambiada_'.
    Por otra parte, he creado una Condicion que escucha dicho evento.
    Al emitirse, ejecuta una funcion
    """

    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def suscribir(self, tipo: str, callback: Callable) -> None:
        if tipo not in self._listeners:
            self._listeners[tipo] = []
        self._listeners[tipo].append(weakref.ref(callback))

    def emitir(self, tipo: str, *args, **kwargs) -> None:
        listeners_vivos = []
        for ref in self._listeners.get(tipo, []):
            callback = ref()
            if callback is not None:
                callback(*args, **kwargs)
                listeners_vivos.append(ref)
        self._listeners[tipo] = listeners_vivos
