# Core/Entities/Mundo/bus_eventos.py
"""
Bus de eventos del mundo. Vive en Core (solo usa librería estándar) para que
Mundo no dependa de Infraestructura.
"""

import inspect
import logging
from typing import Callable
import weakref

logger = logging.getLogger(__name__)


class BusEventos:
    """
    Gestiona los eventos. Ejemplo: Termico emite 'temperatura_cambiada_<id>' y
    una Condicion suscrita a ese evento ejecuta una función al recibirlo.
    """

    def __init__(self):
        self._listeners: dict[str, list] = {}

    def suscribir(self, tipo: str, callback: Callable) -> None:
        """
        Referencia DÉBIL al suscriptor: si su objeto desaparece, la suscripción
        se descarta sola. Los métodos enlazados necesitan WeakMethod (el objeto
        "método" es temporal y un weakref.ref normal moriría al instante).
        Lambdas y funciones locales no se retienen: quien las suscriba debe
        guardar la referencia.
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
        # durante la emisión. Esa suscripción recibe el evento siguiente.
        for ref in list(refs):
            callback = ref()
            if callback is None:
                continue  # el suscriptor ya no existe: se purga abajo
            try:
                callback(*args, **kwargs)
            except Exception:
                # Un suscriptor roto no debe impedir que los demás reciban el evento.
                logger.exception("Suscriptor de '%s' falló.", tipo)

        # Purga EN SITIO: conserva las suscripciones añadidas durante la emisión.
        refs[:] = [ref for ref in refs if ref() is not None]
