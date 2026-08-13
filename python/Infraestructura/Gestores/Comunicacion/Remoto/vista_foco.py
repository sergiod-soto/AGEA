# Infraestructura/Gestores/Comunicacion/Remoto/vista_foco.py
"""
vista_foco.py — FocoBroadcaster: un único vigilante del tick de
Logica_Mundo que reparte (broadcast) la misma actualización a todos
los que estén suscritos, sean el Unity master o cualquier espectador.

Por qué existe como clase con estado y no como función generadora
suelta: la idea de negocio es "una sola conexión lógica a
Logica_Mundo, N Unitys escuchando" — eso obliga a separar quién
FIJA el foco (el master, vía actualizar_foco) de quién lo RECIBE
(cualquier suscriptor, vía suscribirse), y a que solo haya UNA tarea
de fondo vigilando el tick, no una por suscriptor.

Vive junto a comunicaciones_remoto.py para no mezclar esta lógica de
estado/streaming con el dispatch de ejecutar().
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from Infraestructura.Gestores.Comunicacion.Remoto.clientes_remotos import (
    ClientesRemotos,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    comunicacion_remota_service_pb2 as pb,
)

logger = logging.getLogger(__name__)

# Cada cuánto comprueba el vigilante si Logica_Mundo avanzó de tick.
# No es el ritmo de envío (eso lo marca el tick real): es solo la
# frecuencia de "¿ya cambió?".
_POLL_INTERVAL_SEGUNDOS = 0.05


@dataclass
class _FocoParams:
    """Los datos que el master fija con ActualizarFoco."""

    min_pos: tuple[int, int]
    max_pos: tuple[int, int]
    incluir: list[str]
    modo: str


class FocoBroadcaster:
    """
    Estado compartido de "qué se está mostrando ahora mismo". Una
    instancia vive dentro de ComunicacionesRemoto (una por proceso,
    no una por suscriptor).
    """

    def __init__(self, clientes: ClientesRemotos):
        self._clientes = clientes
        self._foco: Optional[_FocoParams] = None
        self._ultimo_tick: Optional[int] = None
        self._suscriptores: set[asyncio.Queue] = set()
        self._tarea_vigilante: Optional[asyncio.Task] = None

    def actualizar_foco(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str],
        modo: str,
    ) -> None:
        """
        Llamado desde ComunicacionesRemoto.actualizar_foco() cuando el
        master manda ActualizarFoco. Solo cambia qué región/filtro se
        usará en el PRÓXIMO tick que se detecte — no dispara un push
        inmediato (el disparo sigue siendo únicamente "hubo tick
        nuevo", según lo decidido).
        """
        self._foco = _FocoParams(min_pos, max_pos, incluir, modo)

    async def suscribirse(self) -> AsyncIterator["pb.ActualizacionFoco"]:
        """
        Un suscriptor nuevo (master o espectador, da igual: reciben
        todos lo mismo). Se le asigna una cola propia donde el
        vigilante deposita cada actualización; este generador solo
        va leyendo de ahí y cediendo al llamador (que es quien
        alimenta el `stream` de gRPC).
        """
        self._asegurar_vigilante()

        cola: asyncio.Queue = asyncio.Queue()
        self._suscriptores.add(cola)
        try:
            while True:
                actualizacion = await cola.get()
                yield actualizacion
        finally:
            # Se ejecuta cuando el cliente gRPC se desconecta (el
            # `async for` de fuera deja de iterar): quitamos su cola
            # para no seguir acumulando actualizaciones para nadie.
            self._suscriptores.discard(cola)

    def _asegurar_vigilante(self) -> None:
        """
        Arranca la única tarea de fondo la primera vez que hace falta
        (primer suscriptor). Si ya está corriendo, no hace nada — así
        no importa cuántos Unitys se conecten, la vigilancia contra
        Logica_Mundo sigue siendo una sola.
        """
        if self._tarea_vigilante is None or self._tarea_vigilante.done():
            self._tarea_vigilante = asyncio.create_task(self._vigilar())

    async def _vigilar(self) -> None:
        """
        Bucle único: mientras haya algún suscriptor y un foco fijado,
        comprueba el tick de Logica_Mundo; si cambió, pide los datos
        del foco UNA vez y los reparte a todas las colas activas.
        """
        while True:
            if not self._suscriptores or self._foco is None:
                # Nadie escuchando, o el master aún no fijó foco:
                # no tiene sentido gastar llamadas a Logica_Mundo.
                await asyncio.sleep(_POLL_INTERVAL_SEGUNDOS)
                continue

            globales_resp = await self._clientes.logica_mundo.get_elementos_globales()
            if not globales_resp.ok:
                logger.warning(
                    "Vista_Foco: GetElementosGlobales devolvió error: %s",
                    globales_resp.error,
                )
                await asyncio.sleep(_POLL_INTERVAL_SEGUNDOS)
                continue

            if globales_resp.tick_actual == self._ultimo_tick:
                await asyncio.sleep(_POLL_INTERVAL_SEGUNDOS)
                continue

            self._ultimo_tick = globales_resp.tick_actual
            foco = (
                self._foco
            )  # copia local por si actualizar_foco() cambia _foco a mitad de fetch

            # Solo se pide `representacion` — se quitó `obtener_celdas_en_region`
            # porque su resultado era redundante con `representacion` (que ya
            # trae lo que Unity necesita para pintar) y mucho más pesado
            # (elemento serializado completo por celda, sin filtrar).
            representacion = await self._clientes.logica_mundo.consultar_representacion(
                foco.min_pos, foco.max_pos, foco.incluir, foco.modo
            )

            actualizacion = pb.ActualizacionFoco(
                ok=True,
                representacion=representacion,
                elementos_globales=globales_resp.elementos_globales,
                tick_actual=self._ultimo_tick,
            )

            # Un solo fetch, repartido a todos: esto es el fan-out.
            for cola in list(self._suscriptores):
                cola.put_nowait(actualizacion)
