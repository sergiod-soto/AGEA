# Infraestructura/Gestores/Mundo/Logica_Mundo/logica_mundo_servicer.py
"""
logica_mundo_servicer.py — Servicer gRPC de LogicaMundoService.

Sigue el mismo patrón de dispatch por NAME que gestor_bots_servicer.py /
gestor_mundo_servicer.py / sector_servicer.py: cada RPC delega en su
módulo de Funciones/, resuelto por nombre en self._dispatch.
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Mundo.Logica_Mundo.logica_mundo import LogicaMundo
from Infraestructura.Gestores.Mundo.Logica_Mundo.registry import FUNCIONES


class LogicaMundoServicer(pb_grpc.LogicaMundoServiceServicer):

    def __init__(self, logica: LogicaMundo) -> None:
        self._logica = logica
        self._dispatch = {fn.NAME: fn for fn in FUNCIONES}

    async def AsignarId(self, request, context):
        return await self._dispatch["AsignarId"].handle(self._logica, request, context)

    async def CrearElemento(self, request, context):
        return await self._dispatch["CrearElemento"].handle(
            self._logica, request, context
        )

    async def ModificarElemento(self, request, context):
        return await self._dispatch["ModificarElemento"].handle(
            self._logica, request, context
        )

    async def EliminarElemento(self, request, context):
        return await self._dispatch["EliminarElemento"].handle(
            self._logica, request, context
        )

    async def ResolverAccion(self, request, context):
        return await self._dispatch["ResolverAccion"].handle(
            self._logica, request, context
        )

    async def SpawnGlobalEvent(self, request, context):
        return await self._dispatch["SpawnGlobalEvent"].handle(
            self._logica, request, context
        )

    async def DespawnGlobalEvent(self, request, context):
        return await self._dispatch["DespawnGlobalEvent"].handle(
            self._logica, request, context
        )

    async def GetActiveEvents(self, request, context):
        return await self._dispatch["GetActiveEvents"].handle(
            self._logica, request, context
        )

    async def ObtenerCeldasEnRegion(self, request, context):
        return await self._dispatch["ObtenerCeldasEnRegion"].handle(
            self._logica, request, context
        )

    async def ActualizarCeldas(self, request, context):
        return await self._dispatch["ActualizarCeldas"].handle(
            self._logica, request, context
        )

    async def ConsultarRepresentacion(self, request, context):
        return await self._dispatch["ConsultarRepresentacion"].handle(
            self._logica, request, context
        )

    async def AvanzarElementosGlobales(self, request, context):
        return await self._dispatch["AvanzarElementosGlobales"].handle(
            self._logica, request, context
        )

    async def SaveSnapshot(self, request, context):
        return await self._dispatch["SaveSnapshot"].handle(
            self._logica, request, context
        )

    async def LoadState(self, request, context):
        return await self._dispatch["LoadState"].handle(self._logica, request, context)

    async def EliminarAvatarBot(self, request, context):
        return await self._dispatch["EliminarAvatarBot"].handle(
            self._logica, request, context
        )
