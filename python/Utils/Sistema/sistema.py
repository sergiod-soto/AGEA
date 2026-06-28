"""
Utils/sistema.py
----------------
Utilidades dependientes del sistema operativo.
"""
import asyncio
import logging
import platform
import signal
from typing import Callable

logger = logging.getLogger(__name__)


def registrar_signals(loop: asyncio.AbstractEventLoop, callback: Callable) -> None:
    """
    Registra SIGINT y SIGTERM de forma compatible con Windows y Linux.

    En Linux usa loop.add_signal_handler (integración nativa con asyncio).
    En Windows usa signal.signal con call_soon_threadsafe para no bloquear el loop.

    callback recibe el objeto signal.Signals como argumento.
    """
    if platform.system() == "Windows":
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(
                sig,
                lambda s, f, _sig=sig: loop.call_soon_threadsafe(
                    callback, signal.Signals(_sig)
                ),
            )
        logger.debug("Signals registradas (Windows): SIGINT, SIGTERM")
    else:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                callback,
                signal.Signals(sig),
            )
        logger.debug("Signals registradas (Linux): SIGINT, SIGTERM")