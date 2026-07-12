# Infraestructura/Gestores/Comunicacion/Remoto/comunicaciones_remoto.py
"""
comunicaciones_remoto.py — Lógica pura de Comunicaciones_Remoto.

Único punto de entrada desde Comunicaciones_Local hacia AWS. Recibe
(componente, operacion, payload) y reenvía al cliente correspondiente,
sin interpretar el contenido del payload más allá de lo que cada
módulo de Funciones/ necesita para esa operación concreta.
"""

from __future__ import annotations

import logging

from Infraestructura.Gestores.Comunicacion.Remoto.clientes_remotos import (
    ClientesRemotos,
)
from Infraestructura.Gestores.Comunicacion.Remoto.registry import FUNCIONES

logger = logging.getLogger(__name__)


class ComunicacionesRemoto:

    def __init__(self, clientes: ClientesRemotos):
        self._clientes = clientes
        self._dispatch = {(fn.COMPONENTE, fn.OPERACION): fn for fn in FUNCIONES}

    async def ejecutar(
        self, componente: str, operacion: str, payload: bytes
    ) -> tuple[bool, str, bytes]:
        """
        ok/error devueltos aquí son del PUENTE — ver docstring del
        módulo. El resultado real de la operación va dentro de
        `payload`, ya serializado como el Response concreto.
        """
        fn = self._dispatch.get((componente, operacion))
        if fn is None:
            logger.warning("Operación desconocida: %s.%s", componente, operacion)
            return False, f"Operación desconocida: {componente}.{operacion}", b""

        try:
            resultado = await fn.handle(self._clientes, payload)
            return True, "", resultado
        except Exception as exc:
            logger.error("Error ejecutando %s.%s: %s", componente, operacion, exc)
            return False, str(exc), b""
