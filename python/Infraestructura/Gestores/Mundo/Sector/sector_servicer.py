# Gestores/Mundo/Sector/sector_servicer.py
import asyncio
import logging
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    sector_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Mundo.Sector.sector import Sector
from Infraestructura.Gestores.Mundo.Sector.registry import FUNCIONES

logger = logging.getLogger(__name__)


class SectorServicer(pb_grpc.SectorServiceServicer):

    def __init__(self, sector: Sector) -> None:
        self._sector = sector
        self._dispatch = {fn.NAME: fn for fn in FUNCIONES}
        # Las operaciones de FASE 0 pueden llegar en paralelo
        self._fase0_lock = asyncio.Lock()

    # ----- añadido: faltaba en el servicer, RPC declarado en el .proto -----
    async def Shutdown(self, request, context):
        return await self._dispatch["Shutdown"].handle(self._sector, request, context)

    async def SetSectorMode(self, request, context):
        return await self._dispatch["SetSectorMode"].handle(
            self._sector, request, context
        )

    async def LoadState(self, request, context):
        return await self._dispatch["LoadState"].handle(self._sector, request, context)

    async def GetState(self, request, context):
        return await self._dispatch["GetState"].handle(self._sector, request, context)

    async def SetGhostZone(self, request, context):
        async with self._fase0_lock:
            return await self._dispatch["SetGhostZone"].handle(
                self._sector, request, context
            )

    async def AddMigratingBot(self, request, context):
        async with self._fase0_lock:
            return await self._dispatch["AddMigratingBot"].handle(
                self._sector, request, context
            )

    async def StartTick(self, request, context):
        return await self._dispatch["StartTick"].handle(self._sector, request, context)

    async def GetDelta(self, request, context):
        return await self._dispatch["GetDelta"].handle(self._sector, request, context)

    async def SaveSnapshot(self, request, context):
        return await self._dispatch["SaveSnapshot"].handle(
            self._sector, request, context
        )

    async def SetSounds(self, request, context):
        return await self._dispatch["SetSounds"].handle(self._sector, request, context)

    # NOTA: GetElementAttributes sigue sin implementar — está declarado en
    # el .proto pero no es parte de "arrancar" (es una consulta de
    # debug/dev sobre elementos, y hoy no hay elementos). Se deja
    # pendiente a propósito, no es un descuido — confirmar si se quiere
    # abordar ahora o más adelante.
