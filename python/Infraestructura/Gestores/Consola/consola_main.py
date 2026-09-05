# Infraestructura/Gestores/Consola/consola_main.py
"""
consola_main.py — Punto de entrada de la consola cuando corre como
PROCESO APARTE (ventana cmd propia en Windows — ver
bootstrap.py::_lanzar_consola). No comparte memoria con el proceso
principal: construye su propia ComunicacionesLocal apuntando a la
misma dirección de Comunicaciones_Remoto que ya conoce el proceso
principal (pasada por variable de entorno, igual que el resto de
componentes en modo local — ver topologia.resolver_env_extra).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

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

    address = os.getenv("COMUNICACIONES_REMOTO_ADDRESS")
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
