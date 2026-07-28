# Infraestructura/Gestores/Comunicacion/Remoto/comunicaciones_remoto.py
"""
comunicaciones_remoto.py — Lógica pura de Comunicaciones_Remoto.

Único punto de entrada desde Comunicaciones_Local hacia AWS. Recibe
(componente, operacion, payload) y reenvía al cliente correspondiente,
sin interpretar el contenido del payload más allá de lo que cada
módulo de Funciones/ necesita para esa operación concreta.

Además de `ejecutar()` (unario, vía el registro FUNCIONES), expone dos
puntos nuevos para Vista_Foco/Unity:
  - `actualizar_foco()`: el master fija qué región/filtro se muestra.
  - `suscribirse_foco()`: cualquiera (master o espectador) se conecta
    a la MISMA emisión — ver FocoBroadcaster en vista_foco.py, que es
    quien realmente lleva el estado y el reparto a los suscriptores.
Ninguno de los dos pasa por `_dispatch`: no son reenvíos a un
componente remoto, son estado y streaming propios de este puente.
"""

from __future__ import annotations

import logging
from typing import AsyncIterator

from Infraestructura.Gestores.Comunicacion.Remoto.clientes_remotos import (
    ClientesRemotos,
)
from Infraestructura.Gestores.Comunicacion.Remoto.registry import FUNCIONES
from Infraestructura.Gestores.Comunicacion.Remoto.vista_foco import FocoBroadcaster
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    comunicacion_remota_service_pb2 as pb,
)

logger = logging.getLogger(__name__)


class ComunicacionesRemoto:

    def __init__(self, clientes: ClientesRemotos):
        self._clientes = clientes
        self._dispatch = {(fn.COMPONENTE, fn.OPERACION): fn for fn in FUNCIONES}
        # Una única instancia por proceso: es el estado compartido de
        # "qué se está mostrando ahora", no algo por suscriptor.
        self._foco = FocoBroadcaster(clientes)

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

    def actualizar_foco(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str],
        modo: str,
    ) -> None:
        """
        Llamado por el servicer al recibir el RPC ActualizarFoco
        (lo manda el master vía Comunicaciones_Local). Es una
        operación local e instantánea: solo actualiza qué región/
        filtro usará el vigilante en el próximo tick, no bloquea ni
        llama a Logica_Mundo.
        """
        self._foco.actualizar_foco(min_pos, max_pos, incluir, modo)

    async def suscribirse_foco(self) -> AsyncIterator["pb.ActualizacionFoco"]:
        """
        Punto de entrada para el RPC de streaming SuscribirseFoco.
        Delega en FocoBroadcaster, que es quien realmente vigila el
        tick y reparte a todos los suscriptores activos.
        """
        async for actualizacion in self._foco.suscribirse():
            yield actualizacion
