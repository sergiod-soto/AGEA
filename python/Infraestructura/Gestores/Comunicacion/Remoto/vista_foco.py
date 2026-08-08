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

Diseño elegido para el primer push tras conectarse (ver discusión):
un suscriptor nuevo recibe la "foto actual" del foco en el primer
poll del vigilante, sin esperar a que Logica_Mundo avance a un tick
posterior a la conexión — igual que conectarte a una webcam: ves el
fotograma de ahora mismo, no esperas al siguiente.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from numpy import uint64

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


class _SuscripcionFoco:
    """
    Iterador async explícito de una suscripción individual al foco.

    Sustituye a un simple generador async (`async def ...: yield ...`)
    porque aclose() sobre un generador que NUNCA llegó a ejecutar su
    primer __anext__() no corre su cuerpo (ni su try/finally) — es una
    particularidad de CPython, no un bug de lógica. El caso real que
    esto cubre: un cliente gRPC que se desconecta antes de recibir su
    primera actualización. Con una clase propia, aclose() siempre da
    de baja la cola, se haya leído algo de ella o no.
    """

    def __init__(self, broadcaster: "FocoBroadcaster", cola: asyncio.Queue):
        self._broadcaster = broadcaster
        self._cola = cola
        self._cerrado = False

    def __aiter__(self) -> "_SuscripcionFoco":
        return self

    async def __anext__(self):
        if self._cerrado:
            raise StopAsyncIteration
        return await self._cola.get()

    async def aclose(self) -> None:
        if not self._cerrado:
            self._cerrado = True
            self._broadcaster._suscriptores.discard(self._cola)


class FocoBroadcaster:
    def __init__(self, clientes: ClientesRemotos):
        self._clientes = clientes
        self._foco: Optional[_FocoParams] = None
        self._ultimo_tick: Optional[int] = None
        self._suscriptores: set[asyncio.Queue] = set()
        self._tarea_vigilante: Optional[asyncio.Task] = None
        self._ultima_actualizacion: Optional["pb.ActualizacionFoco"] = None
        self._version_foco: uint64 = 0
        self._ultima_version_enviada: Optional[int] = None

    def actualizar_foco(self, min_pos, max_pos, incluir, modo) -> None:
        self._foco = _FocoParams(min_pos, max_pos, incluir, modo)
        self._version_foco += 1

    def suscribirse(self) -> AsyncIterator["pb.ActualizacionFoco"]:
        """
        Un suscriptor nuevo (master o espectador, da igual: reciben
        todos lo mismo). Se le asigna una cola propia donde el
        vigilante deposita cada actualización.

        Si ya hay una actualización cacheada (alguien ya recibió al
        menos un frame antes de que este suscriptor llegara), se le
        entrega de inmediato — sin esto, un suscriptor tardío no ve
        nada hasta el próximo tick O próximo cambio de foco, que
        puede tardar arbitrariamente (o no llegar nunca, si nadie
        vuelve a mover la cámara ni el mundo avanza).

        Registra la cola de forma SÍNCRONA al ser llamado — no es
        `async def`. Si lo fuera, la suscripción no quedaría
        contabilizada en _suscriptores hasta el primer `await` sobre
        el generador (los generadores async son perezosos), lo que
        rompe la expectativa de que un suscriptor cuenta desde el
        momento en que se conecta, no desde el momento en que empieza
        a leer.
        """
        self._asegurar_vigilante()
        cola: asyncio.Queue = asyncio.Queue()
        if self._ultima_actualizacion is not None:
            cola.put_nowait(self._ultima_actualizacion)
        self._suscriptores.add(cola)
        return _SuscripcionFoco(self, cola)

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
        while True:
            try:
                await self._ciclo_de_vigilancia()
            except Exception:
                logger.exception(
                    "FocoBroadcaster: error inesperado en el ciclo de vigilancia"
                )
            await asyncio.sleep(_POLL_INTERVAL_SEGUNDOS)

    async def _ciclo_de_vigilancia(self) -> None:
        if not self._suscriptores or self._foco is None:
            return

        globales_resp = await self._clientes.logica_mundo.get_elementos_globales()
        if not globales_resp.ok:
            logger.warning(...)
            return

        tick_cambio = globales_resp.tick_actual != self._ultimo_tick
        foco_cambio = self._version_foco != self._ultima_version_enviada
        if not tick_cambio and not foco_cambio:
            return  # nada nuevo por ninguno de los dos motivos: no repartir

        self._ultimo_tick = globales_resp.tick_actual
        self._ultima_version_enviada = self._version_foco
        foco = self._foco

        celdas = await self._clientes.logica_mundo.obtener_celdas_en_region(
            foco.min_pos, foco.max_pos
        )
        representacion = await self._clientes.logica_mundo.consultar_representacion(
            foco.min_pos, foco.max_pos, foco.incluir, foco.modo
        )

        actualizacion = pb.ActualizacionFoco(
            ok=True,
            celdas=celdas,
            representacion=representacion,
            elementos_globales=globales_resp.elementos_globales,
            tick_actual=self._ultimo_tick,
        )

        self._ultima_actualizacion = actualizacion
        for cola in list(self._suscriptores):
            cola.put_nowait(actualizacion)
