# Infraestructura/Gestores/Comunicacion/Local/comunicaciones_local.py
"""
comunicaciones_local.py — Cliente único hacia Comunicaciones_Remoto.

Es el ÚNICO módulo local con permiso para hablar con AWS. Cualquier
otro módulo local (Vista_Foco, Vision_Unity, Bootstrap para tareas
administrativas) debe pasar por esta clase — nunca abrir un canal
gRPC propio hacia un componente remoto.

Cada método público construye el mensaje *Request tipado del servicio
real (LogicaMundoService / GestorMundoService / GestorBotsService),
lo serializa, lo envía dentro de EjecutarRequest (ver
comunicacion_remota_service.proto), y deserializa la respuesta al
*Response tipado correspondiente.

actualizar_foco / suscribirse_foco son la excepción: no pasan por
EjecutarRequest porque no son un reenvío a un componente remoto —
son RPCs propios de ComunicacionRemotaService (estado y streaming
de Vista_Foco). Se llaman directamente sobre el mismo stub.
"""

from __future__ import annotations

import logging
from typing import AsyncIterator, Optional

import grpc.aio

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    comunicacion_remota_service_pb2 as bridge_pb,
    comunicacion_remota_service_pb2_grpc as bridge_pb_grpc,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Comunicacion import (
    logica_mundo_service_pb2 as logica_pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as mundo_pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Bots import (
    gestor_bots_service_pb2 as bots_pb,
)

logger = logging.getLogger(__name__)


class ComunicacionesLocal:
    """
    address : str   "host:puerto" de Comunicaciones_Remoto (AWS).
    timeout : float segundos de espera por llamada (default 10 s).
    """

    def __init__(self, address: str, timeout: float = 10.0):
        self._address = address
        self._timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub = None

    async def _ensure_channel(self) -> None:
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(self._address)
            self._stub = bridge_pb_grpc.ComunicacionRemotaServiceStub(self._channel)

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None

    async def _ejecutar(self, componente: int, operacion: str, request_msg) -> bytes:
        """
        Envía request_msg (ya construido) serializado dentro de
        EjecutarRequest. Devuelve el payload de la respuesta (bytes) —
        cada método público lo parsea a su *Response concreto.

        Lanza RuntimeError si el PUENTE en sí falló (operación
        desconocida, excepción no controlada en el handler remoto) —
        distinto del ok/error interno de cada *Response, que cada
        método deja pasar tal cual para que el llamante lo interprete.
        """
        await self._ensure_channel()
        req = bridge_pb.EjecutarRequest(
            componente=componente,
            operacion=operacion,
            payload=request_msg.SerializeToString(),
        )
        try:
            resp = await self._stub.Ejecutar(req, timeout=self._timeout)
        except grpc.aio.AioRpcError as exc:
            logger.error("Ejecutar(%s.%s) falló: %s", componente, operacion, exc)
            raise RuntimeError(str(exc)) from exc

        if not resp.ok:
            logger.error(
                "Ejecutar(%s.%s) — el puente reportó error: %s",
                componente,
                operacion,
                resp.error,
            )
            raise RuntimeError(resp.error)

        return resp.payload

    # ------------------------------------------------------------------
    # Logica_Mundo — datos/estado del mundo
    # ------------------------------------------------------------------

    async def consultar_representacion(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str],
        modo: str,
    ) -> "logica_pb.ConsultarRepresentacionResponse":
        req = logica_pb.ConsultarRepresentacionRequest(
            min=common_pb.Position(x=min_pos[0], y=min_pos[1]),
            max=common_pb.Position(x=max_pos[0], y=max_pos[1]),
            incluir=incluir,
            modo=modo,
        )
        payload = await self._ejecutar(
            bridge_pb.LOGICA_MUNDO, "ConsultarRepresentacion", req
        )
        resp = logica_pb.ConsultarRepresentacionResponse()
        resp.ParseFromString(payload)
        return resp

    async def spawn_global_event(
        self, type_: str, pos: Optional[tuple[int, int]], payload: bytes
    ) -> "logica_pb.SpawnGlobalEventResponse":
        event = logica_pb.GlobalEvent(
            type=type_,
            pos=common_pb.Position(x=pos[0], y=pos[1]) if pos else common_pb.Position(),
            payload=payload,
        )
        raw = await self._ejecutar(
            bridge_pb.LOGICA_MUNDO,
            "SpawnGlobalEvent",
            logica_pb.SpawnGlobalEventRequest(event=event),
        )
        resp = logica_pb.SpawnGlobalEventResponse()
        resp.ParseFromString(raw)
        return resp

    async def despawn_global_event(
        self, event_id: str, reason: str
    ) -> tuple[bool, str]:
        req = logica_pb.DespawnGlobalEventRequest(event_id=event_id, reason=reason)
        raw = await self._ejecutar(bridge_pb.LOGICA_MUNDO, "DespawnGlobalEvent", req)
        ack = common_pb.Ack()
        ack.ParseFromString(raw)
        return ack.ok, ack.error

    async def get_active_events(self) -> "logica_pb.GetActiveEventsResponse":
        raw = await self._ejecutar(
            bridge_pb.LOGICA_MUNDO,
            "GetActiveEvents",
            logica_pb.GetActiveEventsRequest(),
        )
        resp = logica_pb.GetActiveEventsResponse()
        resp.ParseFromString(raw)
        return resp

    async def crear_elemento(
        self, pos: tuple[int, int], type_id: str, element: bytes
    ) -> tuple[bool, str]:
        req = logica_pb.CrearElementoRequest(
            pos=common_pb.Position(x=pos[0], y=pos[1]),
            type_id=type_id,
            element=element,
        )
        raw = await self._ejecutar(bridge_pb.LOGICA_MUNDO, "CrearElemento", req)
        ack = common_pb.Ack()
        ack.ParseFromString(raw)
        return ack.ok, ack.error

    async def modificar_elemento(
        self, pos: tuple[int, int], type_id: str, patch: bytes
    ) -> tuple[bool, str]:
        req = logica_pb.ModificarElementoRequest(
            pos=common_pb.Position(x=pos[0], y=pos[1]),
            type_id=type_id,
            patch=patch,
        )
        raw = await self._ejecutar(bridge_pb.LOGICA_MUNDO, "ModificarElemento", req)
        ack = common_pb.Ack()
        ack.ParseFromString(raw)
        return ack.ok, ack.error

    async def eliminar_elemento(
        self, pos: tuple[int, int], element_id: int
    ) -> tuple[bool, str]:
        req = logica_pb.EliminarElementoRequest(
            pos=common_pb.Position(x=pos[0], y=pos[1]),
            element_id=element_id,
        )
        raw = await self._ejecutar(bridge_pb.LOGICA_MUNDO, "EliminarElemento", req)
        ack = common_pb.Ack()
        ack.ParseFromString(raw)
        return ack.ok, ack.error

    # ------------------------------------------------------------------
    # Gestor_Mundo — control del ciclo de tick
    # ------------------------------------------------------------------

    async def pause(self) -> tuple[bool, str]:
        raw = await self._ejecutar(
            bridge_pb.GESTOR_MUNDO, "Pause", mundo_pb.PauseRequest()
        )
        ack = common_pb.Ack()
        ack.ParseFromString(raw)
        return ack.ok, ack.error

    async def resume(self) -> tuple[bool, str]:
        raw = await self._ejecutar(
            bridge_pb.GESTOR_MUNDO, "Resume", mundo_pb.ResumeRequest()
        )
        ack = common_pb.Ack()
        ack.ParseFromString(raw)
        return ack.ok, ack.error

    async def set_tick_rate(self, ticks_per_second: int) -> tuple[bool, str]:
        """
        ticks_per_second <= 0 (usar 0 por convención) pide la frecuencia
        máxima posible: el bucle de Gestor_Mundo deja de dormir entre
        ticks y corre limitado solo por CPU. El cambio se aplica a partir
        del siguiente tick completo, no interrumpe el que esté en curso.
        """
        req = mundo_pb.SetTickRateRequest(ticks_per_second=ticks_per_second)
        raw = await self._ejecutar(bridge_pb.GESTOR_MUNDO, "SetTickRate", req)
        ack = common_pb.Ack()
        ack.ParseFromString(raw)
        return ack.ok, ack.error

    async def trigger_deep_save(self) -> "mundo_pb.TriggerDeepSaveResponse":
        raw = await self._ejecutar(
            bridge_pb.GESTOR_MUNDO, "TriggerDeepSave", mundo_pb.TriggerDeepSaveRequest()
        )
        resp = mundo_pb.TriggerDeepSaveResponse()
        resp.ParseFromString(raw)
        return resp

    async def obtener_elementos_globales(
        self,
    ) -> "logica_pb.GetElementosGlobalesResponse":
        raw = await self._ejecutar(
            bridge_pb.LOGICA_MUNDO,
            "GetElementosGlobales",
            logica_pb.GetElementosGlobalesRequest(),
        )
        resp = logica_pb.GetElementosGlobalesResponse()
        resp.ParseFromString(raw)
        return resp

    async def get_snapshot_info(self) -> "mundo_pb.GetSnapshotInfoResponse":
        raw = await self._ejecutar(
            bridge_pb.GESTOR_MUNDO, "GetSnapshotInfo", mundo_pb.GetSnapshotInfoRequest()
        )
        resp = mundo_pb.GetSnapshotInfoResponse()
        resp.ParseFromString(raw)
        return resp

    # ------------------------------------------------------------------
    # Gestor_Bots — monitorización / administración
    # ------------------------------------------------------------------

    async def list_hypervisors(self) -> "common_pb.HypervisorList":
        raw = await self._ejecutar(
            bridge_pb.GESTOR_BOTS, "ListHypervisors", bots_pb.ListHypervisorsRequest()
        )
        resp = common_pb.HypervisorList()
        resp.ParseFromString(raw)
        return resp

    async def broadcast_budgets(
        self, default_budget: int, overrides: dict[str, int] | None = None
    ) -> tuple[bool, str]:
        entries = [
            common_pb.BudgetEntry(bot_id=bid, budget=pts)
            for bid, pts in (overrides or {}).items()
        ]
        req = bots_pb.BroadcastBudgetsRequest(
            default_budget=default_budget, overrides=entries
        )
        raw = await self._ejecutar(bridge_pb.GESTOR_BOTS, "BroadcastBudgets", req)
        ack = common_pb.Ack()
        ack.ParseFromString(raw)
        return ack.ok, ack.error

    async def freeze_all(self) -> tuple[bool, str]:
        raw = await self._ejecutar(
            bridge_pb.GESTOR_BOTS, "FreezeAll", bots_pb.FreezeAllRequest()
        )
        ack = common_pb.Ack()
        ack.ParseFromString(raw)
        return ack.ok, ack.error

    async def resume_all(self) -> tuple[bool, str]:
        raw = await self._ejecutar(
            bridge_pb.GESTOR_BOTS, "ResumeAll", bots_pb.ResumeAllRequest()
        )
        ack = common_pb.Ack()
        ack.ParseFromString(raw)
        return ack.ok, ack.error

    async def save_snapshot(self, snapshot_id: str) -> tuple[bool, str]:
        req = bots_pb.SaveSnapshotRequest(snapshot_id=snapshot_id)
        raw = await self._ejecutar(bridge_pb.GESTOR_BOTS, "SaveSnapshot", req)
        resp = bots_pb.SaveSnapshotResponse()
        resp.ParseFromString(raw)
        return resp.ok, resp.error

    # ------------------------------------------------------------------
    # Vista_Foco — fijar el foco (master) y suscribirse a él (master
    # y espectadores). No usan _ejecutar(): son RPCs propios de
    # ComunicacionRemotaService, no reenvíos a un componente remoto.
    # ------------------------------------------------------------------

    async def actualizar_foco(
        self,
        min_pos: tuple[int, int],
        max_pos: tuple[int, int],
        incluir: list[str],
        modo: str,
    ) -> tuple[bool, str]:
        """
        Llamado por el master para fijar qué región/filtro debe verse.
        Unario: confirma que el puente lo recibió, no espera datos del
        mundo (esos llegan por el stream de suscribirse_foco).
        """
        await self._ensure_channel()
        req = bridge_pb.FocoRequest(
            min=common_pb.Position(x=min_pos[0], y=min_pos[1]),
            max=common_pb.Position(x=max_pos[0], y=max_pos[1]),
            incluir=incluir,
            modo=modo,
        )
        try:
            resp = await self._stub.ActualizarFoco(req, timeout=self._timeout)
        except grpc.aio.AioRpcError as exc:
            logger.error("ActualizarFoco falló: %s", exc)
            raise RuntimeError(str(exc)) from exc
        return resp.ok, resp.error

    async def suscribirse_foco(
        self,
    ) -> AsyncIterator["bridge_pb.ActualizacionFoco"]:
        """
        Streaming compartido: master y espectadores llaman a este
        mismo método y reciben la misma emisión (ver FocoBroadcaster
        en el lado remoto). El `async for` de quien llame a esto se
        corta solo si el propio llamante deja de iterar o si el canal
        se cae — no hay que cerrarlo a mano en el caso normal.
        """
        await self._ensure_channel()
        try:
            async for actualizacion in self._stub.SuscribirseFoco(
                bridge_pb.SuscribirseFocoRequest()
            ):
                yield actualizacion
        except grpc.aio.AioRpcError as exc:
            logger.error("SuscribirseFoco falló: %s", exc)
            raise RuntimeError(str(exc)) from exc
