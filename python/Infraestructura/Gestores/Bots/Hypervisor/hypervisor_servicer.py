# Gestores/Bots/Hypervisor/hypervisor_servicer.py
"""
Migrado a asyncio (ver hypervisor.py) — todos los métodos pasan a ser
`async def`, con el mismo patrón de dispatch que el resto de servicers
ya asíncronos del sistema.
"""

import logging
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    hypervisor_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Bots.Hypervisor.hypervisor import Hypervisor
from Infraestructura.Gestores.Bots.Hypervisor.registry import FUNCIONES

logger = logging.getLogger(__name__)


class HypervisorServicer(pb_grpc.HypervisorServiceServicer):

    def __init__(self, hypervisor: Hypervisor):
        self._hv = hypervisor
        self._dispatch = {fn.NAME: fn for fn in FUNCIONES}

    async def Shutdown(self, request, context):
        return await self._dispatch["Shutdown"].handle(self._hv, request, context)

    async def SpawnBot(self, request, context):
        return await self._dispatch["SpawnBot"].handle(self._hv, request, context)

    async def KillBot(self, request, context):
        return await self._dispatch["KillBot"].handle(self._hv, request, context)

    async def GetBotStats(self, request, context):
        return await self._dispatch["GetBotStats"].handle(self._hv, request, context)

    async def ListBots(self, request, context):
        return await self._dispatch["ListBots"].handle(self._hv, request, context)

    async def ResetBudgets(self, request, context):
        return await self._dispatch["ResetBudgets"].handle(self._hv, request, context)

    async def SetPointBudget(self, request, context):
        return await self._dispatch["SetPointBudget"].handle(self._hv, request, context)

    async def GetBotStatus(self, request, context):
        return await self._dispatch["GetBotStatus"].handle(self._hv, request, context)

    async def Freeze(self, request, context):
        return await self._dispatch["Freeze"].handle(self._hv, request, context)

    async def Resume(self, request, context):
        return await self._dispatch["Resume"].handle(self._hv, request, context)

    async def SaveSnapshot(self, request, context):
        return await self._dispatch["SaveSnapshot"].handle(self._hv, request, context)
