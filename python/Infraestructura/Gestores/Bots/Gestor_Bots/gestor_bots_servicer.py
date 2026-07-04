"""
gestor_bots_servicer.py
"""

from __future__ import annotations

import logging

from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Bots.Gestor_Bots.gestor_bots import Gestor_Bots
from Infraestructura.Gestores.Bots.Gestor_Bots.registry import FUNCIONES

logger = logging.getLogger(__name__)


class Gestor_Bots_Servicer(pb_grpc.GestorBotsServiceServicer):

    def __init__(self, gestor: Gestor_Bots, hypervisor_client_factory=None):
        self._gestor = gestor
        self._hv_client_factory = hypervisor_client_factory
        self._dispatch = {fn.NAME: fn for fn in FUNCIONES}

    async def SpawnBot(self, request, context):
        return await self._dispatch["SpawnBot"].handle(self._gestor, request, context)

    async def KillBot(self, request, context):
        return await self._dispatch["KillBot"].handle(self._gestor, request, context)

    async def NotifyBotDeath(self, request, context):
        return await self._dispatch["NotifyBotDeath"].handle(
            self._gestor, request, context
        )

    async def BroadcastBudgets(self, request, context):
        return await self._dispatch["BroadcastBudgetsAsync"].handle(
            self._gestor, request, context
        )

    async def ResetBudgets(self, request, context):
        return await self._dispatch["ResetBudgets"].handle(
            self._gestor, request, context
        )

    async def FreezeAll(self, request, context):
        return await self._dispatch["FreezeAll"].handle(self._gestor, request, context)

    async def ResumeAll(self, request, context):
        return await self._dispatch["ResumeAll"].handle(self._gestor, request, context)

    async def SaveSnapshot(self, request, context):
        return await self._dispatch["SaveSnapshot"].handle(
            self._gestor, request, context
        )

    async def LoadState(self, request, context):
        return await self._dispatch["LoadState"].handle(self._gestor, request, context)

    async def RegisterHypervisor(self, request, context):
        ack = await self._dispatch["RegisterHypervisor"].handle(
            self._gestor, request, context
        )
        if ack.ok and self._hv_client_factory is not None:
            client = self._hv_client_factory(request.address, request.port)
            await self._gestor.set_hypervisor_client(request.hypervisor_id, client)
        return ack

    async def UpdateHypervisorLoad(self, request, context):
        return await self._dispatch["UpdateHypervisorLoad"].handle(
            self._gestor, request, context
        )

    async def ListHypervisors(self, request, context):
        return await self._dispatch["ListHypervisors"].handle(
            self._gestor, request, context
        )

    async def ForwardAction(self, request, context):
        return await self._dispatch["ForwardAction"].handle(
            self._gestor, request, context
        )
