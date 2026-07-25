# Infraestructura/Gestores/Mundo/Gestor_Mundo/gestor_mundo_servicer.py


from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Mundo.Gestor_Mundo.gestor_mundo import GestorMundo
from Infraestructura.Gestores.Mundo.Gestor_Mundo.registry import FUNCIONES


class GestorMundoServicer(pb_grpc.GestorMundoServiceServicer):

    def __init__(self, gestor: GestorMundo) -> None:
        self._gestor = gestor
        self._dispatch = {fn.NAME: fn for fn in FUNCIONES}

    # ----- añadido: faltaba en el servicer, RPC declarado en el .proto -----
    async def Shutdown(self, request, context):
        return await self._dispatch["Shutdown"].handle(self._gestor, request, context)

    async def Heartbeat(self, request, context):
        return await self._dispatch["Heartbeat"].handle(self._gestor, request, context)

    async def GetSnapshotInfo(self, request, context):
        return await self._dispatch["GetSnapshotInfo"].handle(
            self._gestor, request, context
        )

    async def Pause(self, request, context):
        return await self._dispatch["Pause"].handle(self._gestor, request, context)

    async def Resume(self, request, context):
        return await self._dispatch["Resume"].handle(self._gestor, request, context)

    async def TriggerDeepSave(self, request, context):
        return await self._dispatch["TriggerDeepSave"].handle(
            self._gestor, request, context
        )

    async def SetTickRate(self, request, context):
        return await self._dispatch["SetTickRate"].handle(
            self._gestor, request, context
        )
