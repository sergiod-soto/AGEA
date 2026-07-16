# Infraestructura/Gestores/Transporte/gestor_mundo_client.py
"""
gestor_mundo_client.py — Cliente async gRPC hacia Gestor_Mundo.
"""

from __future__ import annotations

import logging
from typing import Optional

import grpc.aio

from Infraestructura.Gestores.Transporte.Proto_Generated import common_pb2 as common_pb
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
)
from Infraestructura.Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2_grpc as pb_grpc,
)

logger = logging.getLogger(__name__)


class GestorMundoClient:

    def __init__(self, address: str, timeout: float = 10.0):
        self._address = address
        self._timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub = None

    async def _ensure_channel(self) -> None:
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(self._address)
            self._stub = pb_grpc.GestorMundoServiceStub(self._channel)

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None

    def _t(self, timeout: Optional[float]) -> float:
        return timeout if timeout is not None else self._timeout

    # ------------------------------------------------------------------
    # Infraestructura
    # ------------------------------------------------------------------

    async def heartbeat(
        self, timeout: float | None = None
    ) -> "pb.GestorMundoHeartbeatResponse":
        """
        Llama al RPC Heartbeat real de GestorMundoService. Usado por
        Comunicaciones_Remoto para detectar si este subordinado sigue
        vivo (ver comunicaciones_remoto_servicer.py::Heartbeat).
        """
        await self._ensure_channel()
        return await self._stub.Heartbeat(
            common_pb.HeartbeatRequest(), timeout=self._t(timeout)
        )

    # ------------------------------------------------------------------
    # Control del ciclo de vida
    # ------------------------------------------------------------------

    async def pause(self, timeout: float | None = None) -> tuple[bool, str]:
        await self._ensure_channel()
        try:
            resp = await self._stub.Pause(pb.PauseRequest(), timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("Pause falló: %s", exc)
            return False, str(exc)

    async def resume(self, timeout: float | None = None) -> tuple[bool, str]:
        await self._ensure_channel()
        try:
            resp = await self._stub.Resume(pb.ResumeRequest(), timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("Resume falló: %s", exc)
            return False, str(exc)

    async def set_tick_rate(
        self, ticks_per_second: int, timeout: float | None = None
    ) -> tuple[bool, str]:
        await self._ensure_channel()
        req = pb.SetTickRateRequest(ticks_per_second=ticks_per_second)
        try:
            resp = await self._stub.SetTickRate(req, timeout=self._t(timeout))
            return resp.ok, resp.error
        except grpc.aio.AioRpcError as exc:
            logger.error("SetTickRate falló: %s", exc)
            return False, str(exc)

    async def trigger_deep_save(
        self, timeout: float | None = None
    ) -> "pb.TriggerDeepSaveResponse":
        await self._ensure_channel()
        try:
            return await self._stub.TriggerDeepSave(
                pb.TriggerDeepSaveRequest(), timeout=self._t(timeout)
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("TriggerDeepSave falló: %s", exc)
            return pb.TriggerDeepSaveResponse(ok=False, error=str(exc))

    async def get_snapshot_info(
        self, timeout: float | None = None
    ) -> "pb.GetSnapshotInfoResponse":
        await self._ensure_channel()
        try:
            return await self._stub.GetSnapshotInfo(
                pb.GetSnapshotInfoRequest(), timeout=self._t(timeout)
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("GetSnapshotInfo falló: %s", exc)
            return pb.GetSnapshotInfoResponse(ok=False, error=str(exc))
