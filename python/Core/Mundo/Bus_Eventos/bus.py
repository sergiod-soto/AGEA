from typing import Callable


class BusEventos:
    '''
    Clase encargada de gestionar los eventos.
    
    Ejemplo: 
    
    - El comportamiento termico comprueba si algo ha cambiado de temperatura.
    En caso de asi ser, llama a emitir el evento 'temperatura_cambiada_'.
    Por otra parte, he creado una Condicion que escucha dicho evento.
    Al emitirse, ejecuta una funcion
    '''
    
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def suscribir(self, tipo: str, callback: Callable) -> None:
        if tipo not in self._listeners:
            self._listeners[tipo] = []
        self._listeners[tipo].append(callback)

    def desuscribir(self, tipo: str, callback: Callable) -> None:
        if tipo in self._listeners:
            self._listeners[tipo].remove(callback)
            if not self._listeners[tipo]:
                del self._listeners[tipo]

    def emitir(self, tipo: str, *args, **kwargs) -> None:
        for callback in self._listeners.get(tipo, []):
            callback(*args, **kwargs)
