# Gestores/Mundo/Gestor_Mundo/gestor_mundo_servicer.py
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
from Infraestructura.Gestores.Mundo.Gestor_Mundo.registry import FUNCIONES


class GestorMundoServicer(pb_grpc.GestorMundoServiceServicer):

    def __init__(self, gestor: GestorMundo) -> None:
        self._gestor = gestor
        self._dispatch = {fn.NAME: fn for fn in FUNCIONES}

    async def GetWorldMap(self, request, context):
        async for chunk in self._dispatch["GetWorldMap"].handle(
            self._gestor, request, context
        ):
            yield chunk

    async def GetGlobalState(self, request, context):
        return await self._dispatch["GetGlobalState"].handle(
            self._gestor, request, context
        )

    async def GetSnapshotInfo(self, request, context):
        return await self._dispatch["GetSnapshotInfo"].handle(
            self._gestor, request, context
        )

    async def Pause(self, request, context):
        return await self._dispatch["Pause"].handle(self._gestor, request, context)

    async def Resume(self, request, context):
        return await self._dispatch["Resume"].handle(self._gestor, request, context)

    async def SetTickSpeed(self, request, context):
        return await self._dispatch["SetTickSpeed"].handle(
            self._gestor, request, context
        )

    async def TriggerDeepSave(self, request, context):
        return await self._dispatch["TriggerDeepSave"].handle(
            self._gestor, request, context
        )

    async def SpawnGlobalEvent(self, request, context):
        return await self._dispatch["SpawnGlobalEvent"].handle(
            self._gestor, request, context
        )

    async def DespawnGlobalEvent(self, request, context):
        return await self._dispatch["DespawnGlobalEvent"].handle(
            self._gestor, request, context
        )

    async def GetActiveEvents(self, request, context):
        return await self._dispatch["GetActiveEvents"].handle(
            self._gestor, request, context
        )

    async def ModifyElement(self, request, context):
        return await self._dispatch["ModifyElement"].handle(
            self._gestor, request, context
        )

    async def CreateElement(self, request, context):
        return await self._dispatch["CreateElement"].handle(
            self._gestor, request, context
        )

    async def DeleteElement(self, request, context):
        return await self._dispatch["DeleteElement"].handle(
            self._gestor, request, context
        )

    async def ForwardAction(self, request, context):
        return await self._dispatch["ForwardAction"].handle(
            self._gestor, request, context
        )

    async def SetTickRate(self, request, context):
        return await self._dispatch["SetTickRate"].handle(
            self._gestor, request, context
        )
