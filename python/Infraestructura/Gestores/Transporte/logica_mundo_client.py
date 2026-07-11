# Infraestructura/Gestores/Transporte/logica_mundo_client.py
"""
logica_mundo_client.py — Cliente async gRPC hacia LogicaMundo.

Usado por:
  - Gestor_Mundo   → celdas de región, actualizar celdas, elementos
                      globales, snapshots (ver gestor_mundo.py)
  - Gestor_Bots    → resolver_accion (reenvío de acciones de bots)
  - Comunicacion_Remoto (local) → consultar_representacion, eventos
                      globales, alta/edición/baja de elementos

Mismo patrón que gestor_mundo_client.py / hypervisor_client.py: canal
único, reconexión perezosa, conversión de tipos Python nativos
(tuplas, dicts) a mensajes proto y viceversa, para que quien lo use no
tenga que conocer el formato de transporte.
"""

from __future__ import annotations

import logging
from typing import Optional

import grpc.aio

from Infraestructura.Gestores.tipos_comunes import ActionResult
from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2_grpc as pb_grpc,
)

logger = logging.getLogger(__name__)


class LogicaMundoClient:
    """
    Cliente async gRPC de LogicaMundoService.

    Parámetros
    ----------
    address : str   "host:puerto"
    timeout : float segundos de espera por RPC (default 10 s)
    """

    def __init__(self, address: str, timeout: float = 10.0):
        self._address = address
        self._timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub = None

    async def _ensure_channel(self) -> None:
        """Conexión perezosa — se abre en la primera llamada, no en __init__,
        igual que GestorMundoClient. Evita fallos de arranque si Logica_Mundo
        tarda unos segundos más en estar listo que quien lo consume."""
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(self._address)
            self._stub = pb_grpc.LogicaMundoServiceStub(self._channel)

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None

    def _t(self, timeout: Optional[float]) -> float:
        return timeout if timeout is not None else self._timeout

    @staticmethod
    def _pos_to_pb(pos: tuple[int, int]) -> common_pb.Position:
        x, y = pos
        return common_pb.Position(x=x, y=y)

    @staticmethod
    def _pos_from_pb(pos: common_pb.Position) -> tuple[int, int]:
        return (pos.x, pos.y)

    # ------------------------------------------------------------------
    # Identidad
    # ------------------------------------------------------------------

    async def asignar_id(self, timeout: float | None = None) -> int:
        await self._ensure_channel()
        try:
            resp = await self._stub.AsignarId(
                pb.AsignarIdRequest(), timeout=self._t(timeout)
            )
            return resp.id
        except grpc.aio.AioRpcError as exc:
            logger.error("AsignarId falló: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Elementos
    # ------------------------------------------------------------------

    async def crear_elemento(
        self,
        pos: tuple[int, int],
        type_id: str,
        element: bytes,
        timeout: float | None = None,
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.CrearElementoRequest(
            pos=self._pos_to_pb(pos), type_id=type_id, element=element
        )
        try:
            resp = await self._stub.CrearElemento(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("CrearElemento falló: %s", exc)
            return False, str(exc)

    async def modificar_elemento(
        self,
        pos: tuple[int, int],
        type_id: str,
        patch: bytes,
        timeout: float | None = None,
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.ModificarElementoRequest(
            pos=self._pos_to_pb(pos), type_id=type_id, patch=patch
        )
        try:
            resp = await self._stub.ModificarElemento(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("ModificarElemento falló: %s", exc)
            return False, str(exc)

    async def eliminar_elemento(
        self, pos: tuple[int, int], timeout: float | None = None
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.EliminarElementoRequest(pos=self._pos_to_pb(pos))
        try:
            resp = await self._stub.EliminarElemento(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("EliminarElemento falló: %s", exc)
            return False, str(exc)

    # ------------------------------------------------------------------
    # Acciones de bots
    # ------------------------------------------------------------------

    async def resolver_accion(
        self,
        bot_id: str,
        action_type: str,
        payload: bytes = b"",
        timeout: float | None = None,
    ) -> ActionResult:
        await self._ensure_channel()
        req = pb.ResolverAccionRequest(
            bot_id=bot_id, action_type=action_type, payload=payload
        )
        try:
            resp = await self._stub.ResolverAccion(req, timeout=self._t(timeout))
            return ActionResult(
                ok=resp.ok,
                payload=resp.payload,
                error=resp.error,
                world_tick=resp.world_tick,
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("ResolverAccion falló: %s", exc)
            return ActionResult(ok=False, error=str(exc))

    # ------------------------------------------------------------------
    # Eventos globales
    # ------------------------------------------------------------------

    async def spawn_global_event(
        self,
        event_id: str,
        type_: str,
        pos: Optional[tuple[int, int]],
        payload: bytes,
        timeout: float | None = None,
    ) -> tuple[bool, str, str]:
        await self._ensure_channel()
        event = pb.GlobalEvent(
            event_id=event_id,
            type=type_,
            pos=self._pos_to_pb(pos) if pos is not None else common_pb.Position(),
            payload=payload,
        )
        try:
            resp = await self._stub.SpawnGlobalEvent(
                pb.SpawnGlobalEventRequest(event=event), timeout=self._t(timeout)
            )
            return resp.ok, resp.error, resp.event_id
        except grpc.aio.AioRpcError as exc:
            logger.error("SpawnGlobalEvent falló: %s", exc)
            return False, str(exc), ""

    async def despawn_global_event(
        self, event_id: str, reason: str, timeout: float | None = None
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.DespawnGlobalEventRequest(event_id=event_id, reason=reason)
        try:
            resp = await self._stub.DespawnGlobalEvent(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("DespawnGlobalEvent falló: %s", exc)
            return False, str(exc)

    async def get_active_events(self, timeout: float | None = None) -> list:
        await self._ensure_channel()
        try:
            resp = await self._stub.GetActiveEvents(
                pb.GetActiveEventsRequest(), timeout=self._t(timeout)
            )
            return list(resp.events)
        except grpc.aio.AioRpcError as exc:
            logger.error("GetActiveEvents falló: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Soporte al ciclo de tick de Gestor_Mundo
    # ------------------------------------------------------------------

    async def obtener_celdas_en_region(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        excluir_min: Optional[tuple[int, int]] = None,
        excluir_max: Optional[tuple[int, int]] = None,
        timeout: float | None = None,
    ) -> list:
        """Devuelve una lista de common_pb2.Cell — Gestor_Mundo las usa
        tal cual (proto), sin interpretarlas."""
        await self._ensure_channel()

        tiene_exclusion = excluir_min is not None and excluir_max is not None
        req = pb.ObtenerCeldasEnRegionRequest(
            min=self._pos_to_pb(min_pos),
            max=self._pos_to_pb(max_pos),
            tiene_exclusion=tiene_exclusion,
        )
        if tiene_exclusion:
            req.excluir_min.CopyFrom(self._pos_to_pb(excluir_min))
            req.excluir_max.CopyFrom(self._pos_to_pb(excluir_max))

        try:
            resp = await self._stub.ObtenerCeldasEnRegion(req, timeout=self._t(timeout))
            if not resp.ok:
                logger.warning("ObtenerCeldasEnRegion respondió error: %s", resp.error)
                return []
            return list(resp.cells)
        except grpc.aio.AioRpcError as exc:
            logger.error("ObtenerCeldasEnRegion falló: %s", exc)
            return []

    async def actualizar_celdas(
        self, changed_cells: list, timeout: float | None = None
    ) -> bool:
        """changed_cells: lista de common_pb2.Cell tal como llegan de
        sector.GetDelta — se reenvían sin traducir."""
        await self._ensure_channel()
        req = pb.ActualizarCeldasRequest(changed_cells=changed_cells)
        try:
            resp = await self._stub.ActualizarCeldas(req, timeout=self._t(timeout))
            return resp.ok
        except grpc.aio.AioRpcError as exc:
            logger.error("ActualizarCeldas falló: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Representación (Vista_Foco / Unity)
    # ------------------------------------------------------------------

    async def consultar_representacion(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str],
        modo: str,
        timeout: float | None = None,
    ) -> bytes:
        await self._ensure_channel()
        req = pb.ConsultarRepresentacionRequest(
            min=self._pos_to_pb(min_pos),
            max=self._pos_to_pb(max_pos),
            incluir=incluir,
            modo=modo,
        )
        try:
            resp = await self._stub.ConsultarRepresentacion(
                req, timeout=self._t(timeout)
            )
            if not resp.ok:
                logger.warning(
                    "ConsultarRepresentacion respondió error: %s", resp.error
                )
                return b""
            return resp.datos
        except grpc.aio.AioRpcError as exc:
            logger.error("ConsultarRepresentacion falló: %s", exc)
            return b""

    # ------------------------------------------------------------------
    # Elementos globales de tick (avanzar ciclo día-noche, lunar...)
    # ------------------------------------------------------------------

    async def avanzar_elementos_globales(
        self, tick_id: int, timeout: float | None = None
    ) -> dict:

        raise NotImplementedError(
            "Falta el RPC AvanzarElementosGlobales en logica_mundo_service.proto"
        )

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    async def save_snapshot(
        self, snapshot_id: str, timeout: float | None = None
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.SaveSnapshotRequest(snapshot_id=snapshot_id)
        try:
            resp = await self._stub.SaveSnapshot(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("SaveSnapshot falló: %s", exc)
            return False, str(exc)

    async def load_state(self, snapshot_id: str, timeout: float | None = None) -> bool:
        await self._ensure_channel()
        req = pb.LoadStateRequest(snapshot_id=snapshot_id)
        try:
            resp = await self._stub.LoadState(req, timeout=self._t(timeout))
            return resp.ok
        except grpc.aio.AioRpcError as exc:
            logger.error("LoadState falló: %s", exc)
            return False
