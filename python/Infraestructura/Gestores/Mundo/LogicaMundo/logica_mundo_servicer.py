# Infraestructura/Gestores/Mundo/LogicaMundo/logica_mundo_servicer.py
"""
logica_mundo_servicer.py — Servicer gRPC de LogicaMundoService.

Sigue el mismo patrón de dispatch por NAME que gestor_bots_servicer.py /
gestor_mundo_servicer.py / sector_servicer.py: cada RPC delega en su
módulo de Funciones/, resuelto por nombre en self._dispatch.

Shutdown añadido: faltaba en el servicer, aunque el RPC ya estaba
declarado en logica_mundo_service.proto (confirmado).

AvanzarTick añadido: el RPC existía en el proto y en el registry, pero
el servicer no tenía el método, así que gRPC usaba el del servicer base
(NotImplementedError / UNIMPLEMENTED).
"""

from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2_grpc as pb_grpc,
)
from Infraestructura.Gestores.Mundo.LogicaMundo.logica_mundo import LogicaMundo
from Infraestructura.Gestores.Mundo.LogicaMundo.registry import FUNCIONES


class LogicaMundoServicer(pb_grpc.LogicaMundoServiceServicer):

    def __init__(self, logica: LogicaMundo) -> None:
        self._logica = logica
        # Índice NAME -> módulo. Cada método de abajo busca aquí su
        # implementación; si un módulo no está en FUNCIONES (registry.py),
        # el método falla con KeyError al llamarse.
        self._dispatch = {fn.NAME: fn for fn in FUNCIONES}
        

    async def Shutdown(self, request, context):
        return await self._dispatch["Shutdown"].handle(self._logica, request, context)

    async def Heartbeat(self, request, context):
        return await self._dispatch["Heartbeat"].handle(self._logica, request, context)

    async def AsignarId(self, request, context):
        return await self._dispatch["AsignarId"].handle(self._logica, request, context)

    async def CrearElemento(self, request, context):
        return await self._dispatch["CrearElemento"].handle(
            self._logica, request, context
        )

    async def ConstruirElemento(self, request, context):
        return await self._dispatch["ConstruirElemento"].handle(
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

    async def GetElementosGlobales(self, request, context):
        return await self._dispatch["GetElementosGlobales"].handle(
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

    async def ObtenerCeldasAtmosferaEnRegion(self, request, context):
        return await self._dispatch["ObtenerCeldasAtmosferaEnRegion"].handle(
            self._logica, request, context
        )

    async def ActualizarCeldasAtmosfera(self, request, context):
        return await self._dispatch["ActualizarCeldasAtmosfera"].handle(
            self._logica, request, context
        )

    async def ObtenerProgresoCiclos(self, request, context):
        return await self._dispatch["ObtenerProgresoCiclos"].handle(
            self._logica, request, context
        )

    async def ConsultarRepresentar(self, request, context):
        return await self._dispatch["ConsultarRepresentar"].handle(
            self._logica, request, context
        )

    async def AvanzarTick(self, request, context):
        # Avanza el tiempo del mundo (tick actual + reloj). Independiente
        # de los elementos globales: ver Funciones/avanzar_tick.py.
        return await self._dispatch["AvanzarTick"].handle(
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

    async def MatarBot(self, request, context):
        return await self._dispatch["MatarBot"].handle(self._logica, request, context)

    async def GenerarMundo(self, request, context):
        return await self._dispatch["GenerarMundo"].handle(
            self._logica, request, context
        )

    async def EstadoGeneracionMundo(self, request, context):
        return await self._dispatch["EstadoGeneracionMundo"].handle(
            self._logica, request, context
        )

    async def ObtenerAudio(self, request, context):
        return await self._dispatch["ObtenerAudio"].handle(
            self._logica, request, context
        )

    async def EjecutarComandoConsola(self, request, context):
        from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
            logica_mundo_service_pb2 as pb,
        )
        from Infraestructura.Gestores.Mundo.LogicaMundo.ComandosConsola.registry_consola import (
            COMANDOS_CONSOLA,
        )

        handler = COMANDOS_CONSOLA.get(request.tipo)
        if handler is None:
            return pb.ComandoConsolaResponse(
                ok=False, error=f"Comando de consola desconocido: {request.tipo}"
            )
        try:
            payload = await handler.handle(self._logica, request.payload)
            return pb.ComandoConsolaResponse(ok=True, error="", payload=payload)
        except Exception as e:
            return pb.ComandoConsolaResponse(ok=False, error=str(e), payload=b"")

    async def ObtenerBotsEnRegion(self, request, context):
        return await self._dispatch["ObtenerBotsEnRegion"].handle(
            self._logica, request, context
        )
