# Infraestructura/Gestores/Consola/consola_main.py
"""
consola_main.py — Punto de entrada de la consola cuando corre como
PROCESO APARTE (ventana cmd propia en Windows — ver
bootstrap.py::_lanzar_consola).

Se añade también un input() final si algo falla, para que la ventana
no vuelva a desaparecer sin dar tiempo a leer el error, sea cual sea
la causa real.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path

from Config.settings import COMUNICACIONES_REMOTO_ADDRESS

# Debe ir ANTES de cualquier import "Infraestructura...." — ver docstring.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("consola_main")


async def _main() -> None:
    from Infraestructura.Gestores.Comunicacion.Local.comunicaciones_local import (
        ComunicacionesLocal,
    )
    from Infraestructura.Gestores.Consola.consola import iniciar

    address = COMUNICACIONES_REMOTO_ADDRESS
    if not address:
        logger.error(
            "COMUNICACIONES_REMOTO_ADDRESS no está definida. "
            "Esta consola debe lanzarse desde bootstrap.py, no a mano."
        )
        sys.exit(1)

    comunicaciones = ComunicacionesLocal(address)
    try:
        await iniciar(comunicaciones)
    finally:
        await comunicaciones.close()


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass
    except SystemExit:
        raise
    except Exception:
        # Red de seguridad: si algo revienta antes/durante _main(), se
        # imprime el traceback completo y se espera a que pulses Enter,
        # en vez de dejar que la ventana se cierre sola. Ver docstring.
        traceback.print_exc()
        input("\nLa consola terminó con un error. Pulsa Enter para cerrar...")
