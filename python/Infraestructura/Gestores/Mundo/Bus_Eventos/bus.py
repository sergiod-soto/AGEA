# Infraestructura/Gestores/Mundo/Bus_Eventos/bus.py


import inspect
import logging
from typing import Callable
import weakref

logger = logging.getLogger(__name__)


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
        """
        Referencia DÉBIL al suscriptor: si su objeto desaparece, la suscripción
        se descarta sola. Los métodos enlazados (self.metodo) necesitan
        WeakMethod: el objeto "método" es temporal y un weakref.ref normal
        moriría al instante. Lambdas y funciones locales no se retienen: quien
        las suscriba debe guardar la referencia.
        """
        if inspect.ismethod(callback):
            ref = weakref.WeakMethod(callback)
        else:
            ref = weakref.ref(callback)
        self._listeners.setdefault(tipo, []).append(ref)

    def emitir(self, tipo: str, *args, **kwargs) -> None:
        refs = self._listeners.get(tipo)
        if not refs:
            return  # nadie escucha: no se crea la clave

        # Se itera sobre una COPIA: un suscriptor puede llamar a suscribir()
        # durante la emisión y eso modifica `refs`. Esa nueva suscripción
        # recibirá el evento siguiente, no este.
        for ref in list(refs):
            callback = ref()
            if callback is None:
                continue  # el suscriptor ya no existe: se purga abajo
            try:
                callback(*args, **kwargs)
            except Exception:
                # Un suscriptor roto no debe impedir que los demás reciban el evento.
                logger.exception("Suscriptor de '%s' falló.", tipo)

        # Purga de referencias muertas EN SITIO: conserva las suscripciones
        # añadidas durante la emisión (antes se reemplazaba la lista y se perdían).
        refs[:] = [ref for ref in refs if ref() is not None]
