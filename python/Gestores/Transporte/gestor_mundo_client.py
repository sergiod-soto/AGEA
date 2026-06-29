# Gestores/Transporte/gestor_mundo_client.py
"""
gestor_mundo_client.py
----------------------
Cliente async gRPC hacia GestorMundo.
Usado por GestorBots para reenviar acciones de bots al Mundo.
"""

import logging
from dataclasses import dataclass

import grpc.aio

from Gestores.Mundo.Gestor_Mundo.gestor_mundo import ActionResult
from Gestores.Transporte.Proto_Generated.Sectores import (
    gestor_mundo_service_pb2 as pb,
    gestor_mundo_service_pb2_grpc as pb_grpc,
)

logger = logging.getLogger(__name__)


class GestorMundoClient:
    def __init__(self, address: str, timeout: float = 2.0):
        self._address = address
        self._timeout = timeout
        self._channel: grpc.aio.Channel | None = None
        self._stub = None

    async def _ensure_channel(self) -> None:
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(self._address)
            self._stub = pb_grpc.GestorMundoServiceStub(self._channel)

    async def forward_action(
        self, bot_id: str, action_type: str, payload: bytes = b""
    ) -> ActionResult:
        await self._ensure_channel()
        request = pb.ForwardActionRequest(
            bot_id=bot_id,
            action_type=action_type,
            payload=payload,
        )
        try:
            resp = await self._stub.ForwardAction(request, timeout=self._timeout)
            return ActionResult(
                ok=resp.ok,
                payload=resp.payload,
                error=resp.error,
                world_tick=resp.tick_id,
            )
        except grpc.aio.AioRpcError as exc:
            logger.error("GestorMundoClient.forward_action error: %s", exc)
            return ActionResult(ok=False, error=str(exc))

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None

    async def notify_bot_death(self, bot_id: str, cause: str, tick: int) -> None:
        await self._ensure_channel()
        request = pb.BotDeathNotification(
            bot_id=bot_id,
            cause=cause,
            tick=tick,
        )
        try:
            await self._stub.NotifyBotDeath(request, timeout=self._timeout)
        except grpc.aio.AioRpcError as exc:
            logger.error("GestorMundoClient.notify_bot_death error: %s", exc)
