# Infraestructura/Gestores/Transporte/gestor_mundo_client.py
"""
gestor_mundo_client.py — Cliente async gRPC hacia Gestor_Mundo.

Reescrito tras el refactor a Logica_Mundo: forward_action y
notify_bot_death quedaron obsoletos (esas operaciones ya no viven en
GestorMundoService, ver logica_mundo_client.py) y se retiran de aquí.

Este cliente pasa a envolver las operaciones de administración del
ciclo de tick que Comunicaciones_Remoto necesita reenviar cuando
Comunicaciones_Local se lo pide (Pause/Resume/SetTickRate/
TriggerDeepSave/GetGlobalState/GetSnapshotInfo) — mismo servidor de
siempre (GestorMundoService), solo que hasta ahora nadie los envolvía
en un cliente Python.
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
    """
    Cliente async gRPC de GestorMundoService.

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
        """Conexión perezosa — mismo patrón que el resto de clientes
        async del proyecto (evita fallos de arranque por orden de
        arranque entre procesos)."""
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
        """
        Devuelve la respuesta proto tal cual (ok/error/snapshot_id) — no
        se reduce a una tupla porque Comunicaciones_Remoto la reenvía
        serializada sin más interpretación (ver Ejecutar en el proto
        puente), igual que ya hace obtener_celdas_en_region con Cell.
        """
        await self._ensure_channel()
        try:
            return await self._stub.TriggerDeepSave(
                pb.TriggerDeepSaveRequest(), timeout=self._t(timeout)
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("TriggerDeepSave falló: %s", exc)
            return pb.TriggerDeepSaveResponse(ok=False, error=str(exc))

    # ------------------------------------------------------------------
    # Consulta del mundo
    # ------------------------------------------------------------------

    async def get_global_state(
        self, timeout: float | None = None
    ) -> "pb.GetGlobalStateResponse":
        await self._ensure_channel()
        try:
            return await self._stub.GetGlobalState(
                pb.GetGlobalStateRequest(), timeout=self._t(timeout)
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("GetGlobalState falló: %s", exc)
            return pb.GetGlobalStateResponse(ok=False, error=str(exc))

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
