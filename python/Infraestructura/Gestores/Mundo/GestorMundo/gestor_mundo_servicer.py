# Infraestructura/Gestores/Mundo/GestorMundo/gestor_mundo_servicer.py


from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Mundo.GestorMundo.gestor_mundo import GestorMundo
from Infraestructura.Gestores.Mundo.GestorMundo.registry import FUNCIONES


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

    async def EjecutarComandoConsola(self, request, context):
        from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
            gestor_mundo_service_pb2 as pb,
        )
        from Infraestructura.Gestores.Mundo.GestorMundo.ComandosConsola.registry_consola import (
            COMANDOS_CONSOLA,
        )

        handler = COMANDOS_CONSOLA.get(request.tipo)
        if handler is None:
            return pb.ComandoConsolaResponse(
                ok=False, error=f"Comando de consola desconocido: {request.tipo}"
            )
        try:
            payload = await handler.handle(self._gestor, request.payload)
            return pb.ComandoConsolaResponse(ok=True, error="", payload=payload)
        except Exception as e:
            return pb.ComandoConsolaResponse(ok=False, error=str(e), payload=b"")
